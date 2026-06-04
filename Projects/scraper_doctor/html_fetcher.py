"""
html_fetcher.py — Captura de HTML por URL de forma genérica.

Responsabilidade única: dado uma URL, retorna o HTML dessa página.
Não conhece o fluxo do scraper — apenas captura o que lhe é pedido.

Estratégia:
1. Tenta requests.get() — rápido, sem browser
2. Se redirect para login / 401 / 403: usa Selenium com credenciais do .env
3. Salva HTML em html/<nome>.html
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv

from config import HTML_DIR

load_dotenv(Path(__file__).parent / ".env")

TARGET_USERNAME = os.environ.get("TARGET_USERNAME", "")
TARGET_PASSWORD = os.environ.get("TARGET_PASSWORD", "")


def fetch_html(
    url: str,
    name: str,
    use_selenium: bool = False,
    headless: bool = True,
    post_load_wait: float = 2.0,
) -> Path | None:
    """
    Captura o HTML de uma URL e salva em html/<name>.html.

    Args:
        url: URL a capturar
        name: nome base do arquivo (sem .html)
        use_selenium: força uso do Selenium mesmo em páginas públicas
        headless: modo headless do Chrome
        post_load_wait: segundos de espera após carregamento

    Returns:
        Path do arquivo HTML salvo, ou None se falhou
    """
    if use_selenium:
        return _fetch_with_selenium(url, name, headless, post_load_wait)

    # Tenta requests primeiro
    result = _fetch_with_requests(url, name)
    if result:
        return result

    # Fallback para Selenium
    print(f"  [FETCHER] requests falhou — tentando Selenium para {url}")
    return _fetch_with_selenium(url, name, headless, post_load_wait)


def _fetch_with_requests(url: str, name: str) -> Path | None:
    """Captura via requests — sem browser, sem JavaScript."""
    try:
        import requests

        resp = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            allow_redirects=True,
        )

        # Indica que precisa de autenticação
        if resp.status_code in (401, 403) or "login" in resp.url.lower():
            return None

        if resp.status_code != 200:
            return None

        path = HTML_DIR / f"{name}.html"
        path.write_text(resp.text, encoding="utf-8")
        print(f"  [FETCHER] {url} → {path.name} ({len(resp.text):,} chars) via requests")
        return path

    except Exception as e:
        print(f"  [FETCHER] requests erro: {e}")
        return None


def _fetch_with_selenium(
    url: str,
    name: str,
    headless: bool,
    wait_seconds: float,
) -> Path | None:
    """Captura via Selenium — suporta JavaScript e autenticação."""
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait

    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(wait_seconds)

        path = HTML_DIR / f"{name}.html"
        path.write_text(driver.page_source, encoding="utf-8")
        print(f"  [FETCHER] {url} → {path.name} ({len(driver.page_source):,} chars) via Selenium")
        return path

    except Exception as e:
        print(f"  [FETCHER] Selenium erro: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def fetch_authenticated(
    url: str,
    name: str,
    login_url: str,
    login_actions: list[dict],
    headless: bool = True,
    post_login_wait: float = 4.0,
    post_page_wait: float = 2.0,
) -> Path | None:
    """
    Captura HTML de uma página que requer autenticação.

    Executa as ações de login informadas antes de acessar a URL alvo.

    Args:
        url: URL da página a capturar após login
        name: nome base do arquivo HTML
        login_url: URL da página de login
        login_actions: lista de ações para executar na página de login
            Ex: [
                {"action": "send_keys", "selector": ("ID", "username"), "value": "${USERNAME}"},
                {"action": "send_keys", "selector": ("ID", "password"), "value": "${PASSWORD}"},
                {"action": "click", "selector": ("ID", "loginBtn")},
            ]
        headless: modo headless
        post_login_wait: espera após submeter login
        post_page_wait: espera após carregar a página alvo

    Returns:
        Path do HTML salvo ou None se falhou
    """
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    STRATEGY_MAP = {
        "ID": By.ID,
        "XPATH": By.XPATH,
        "CLASS_NAME": By.CLASS_NAME,
        "CSS_SELECTOR": By.CSS_SELECTOR,
        "NAME": By.NAME,
    }

    def resolve(value: str) -> str:
        return (
            value
            .replace("${USERNAME}", TARGET_USERNAME)
            .replace("${PASSWORD}", TARGET_PASSWORD)
        )

    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 30)

        # Login
        driver.get(login_url)
        time.sleep(1)

        for action in login_actions:
            act = action["action"]
            strategy_name, sel_value = action["selector"]
            strategy = STRATEGY_MAP.get(strategy_name, By.ID)
            value = resolve(action.get("value", ""))

            if act == "send_keys":
                wait.until(
                    EC.presence_of_element_located((strategy, sel_value))
                ).send_keys(value)
            elif act == "click":
                wait.until(
                    EC.element_to_be_clickable((strategy, sel_value))
                ).click()
            elif act == "wait":
                time.sleep(float(value))

        time.sleep(post_login_wait)

        # Navega para a página alvo se diferente da de login
        if url != login_url:
            driver.get(url)
            time.sleep(post_page_wait)

        path = HTML_DIR / f"{name}.html"
        path.write_text(driver.page_source, encoding="utf-8")
        print(f"  [FETCHER] {url} → {path.name} ({len(driver.page_source):,} chars) autenticado")
        return path

    except Exception as e:
        print(f"  [FETCHER] fetch_authenticated erro: {e}")
        return None
    finally:
        if driver:
            driver.quit()