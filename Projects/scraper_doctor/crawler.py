"""
crawler.py — Navegação autenticada no sistema alvo para captura de HTML por etapa.

Usa Selenium para replicar o fluxo do scraper original, capturando o HTML
de cada página antes de interagir. Alimenta o comparator.py com HTMLs reais.

Credenciais lidas do arquivo .env (nunca hardcoded).
"""

import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import HTML_DIR

load_dotenv(Path(__file__).parent / ".env")

TARGET_URL = os.environ.get("TARGET_URL", "")
TARGET_USERNAME = os.environ.get("TARGET_USERNAME", "")
TARGET_PASSWORD = os.environ.get("TARGET_PASSWORD", "")

WAIT_TIMEOUT = 30  # segundos por elemento


@dataclass
class CrawlResult:
    """HTML capturado em cada etapa da navegação."""
    pages: dict[str, Path] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"Páginas capturadas: {len(self.pages)}"]
        for name, path in self.pages.items():
            size = path.stat().st_size
            lines.append(f"  {name:<30} → {path.name} ({size:,} bytes)")
        if self.errors:
            lines.append(f"\nErros ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"  {e}")
        return "\n".join(lines)


def _save_html(driver, name: str) -> Path:
    """Salva o HTML atual do driver em html/<name>.html."""
    path = HTML_DIR / f"{name}.html"
    path.write_text(driver.page_source, encoding="utf-8")
    print(f"  [HTML] Salvo: {path.name} ({len(driver.page_source):,} chars)")
    return path


def _build_driver(headless: bool = True) -> webdriver.Chrome:
    """Inicializa o Chrome com gerenciamento automático de driver (Selenium Manager)."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def _load_crawler_config(config_path: str | None = None) -> dict | None:
    """
    Carrega configuração YAML do crawler se disponível.
    Retorna None se não encontrar arquivo — mantém comportamento atual.
    """
    candidates = [
        config_path,
        "crawler_config.yaml",
        "crawler_config.yml",
    ]

    for path in candidates:
        if path and Path(path).exists():
            try:
                import yaml
                with open(path, encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                print(f"[CRAWLER] Configuração carregada: {path}")
                return config
            except ImportError:
                print("[CRAWLER] PyYAML não instalado — usando fluxo hardcoded.")
                return None
            except Exception as e:
                print(f"[CRAWLER] Erro ao ler {path}: {e}")
                return None

    return None


def _execute_config_stage(
    stage: dict,
    driver,
    wait,
    result: CrawlResult,
) -> bool:
    """
    Executa uma etapa definida no crawler_config.yaml.
    Retorna True se bem-sucedida, False se falhou.
    """
    import time as time_mod

    stage_name = stage.get("name", "unknown")
    actions = stage.get("actions", [])
    save_html = stage.get("save_html", False)

    STRATEGY_MAP = {
        "ID": By.ID,
        "XPATH": By.XPATH,
        "CLASS_NAME": By.CLASS_NAME,
        "CSS_SELECTOR": By.CSS_SELECTOR,
        "NAME": By.NAME,
    }

    def resolve(value: str) -> str:
        for key in ["TARGET_URL", "TARGET_USERNAME", "TARGET_PASSWORD"]:
            value = value.replace(f"${{{key}}}", os.environ.get(key, ""))
        return value

    try:
        for action in actions:
            act = action.get("action")
            sel_conf = action.get("selector", {})
            value = resolve(str(action.get("value", "")))

            if act == "get":
                driver.get(value)
            elif act == "wait":
                time_mod.sleep(float(value))
            elif act == "send_keys":
                strategy = STRATEGY_MAP.get(sel_conf.get("strategy", "ID"), By.ID)
                wait.until(
                    EC.presence_of_element_located((strategy, sel_conf.get("value", "")))
                ).send_keys(value)
            elif act == "click":
                strategy = STRATEGY_MAP.get(sel_conf.get("strategy", "ID"), By.ID)
                wait.until(
                    EC.element_to_be_clickable((strategy, sel_conf.get("value", "")))
                ).click()
            elif act == "click_js":
                strategy = STRATEGY_MAP.get(sel_conf.get("strategy", "ID"), By.ID)
                element = wait.until(
                    EC.element_to_be_clickable((strategy, sel_conf.get("value", "")))
                )
                driver.execute_script("arguments[0].click();", element)
            elif act == "wait_for":
                strategy = STRATEGY_MAP.get(sel_conf.get("strategy", "ID"), By.ID)
                wait.until(
                    EC.presence_of_element_located((strategy, sel_conf.get("value", "")))
                )
            elif act == "select":
                from selenium.webdriver.support.ui import Select
                strategy = STRATEGY_MAP.get(sel_conf.get("strategy", "ID"), By.ID)
                element = wait.until(
                    EC.presence_of_element_located((strategy, sel_conf.get("value", "")))
                )
                Select(element).select_by_value(value)

        if save_html:
            result.pages[stage_name] = _save_html(driver, stage_name)

        return True

    except Exception as e:
        result.errors.append(f"{stage_name} falhou: {e}")
        if save_html:
            result.pages[f"{stage_name}_error"] = _save_html(driver, f"{stage_name}_error")
        return False


def crawl(headless: bool = True, config_path: str | None = None) -> CrawlResult:
    """
    Navega pelo sistema alvo replicando o fluxo do scraper original.
    Captura o HTML em cada etapa antes de interagir.

    Args:
        headless: se False, abre janela do Chrome (útil para debug)
        config_path: caminho para um crawler_config.yaml alternativo

    Returns:
        CrawlResult com os HTMLs capturados e erros encontrados
    """
    result = CrawlResult()

    if not TARGET_USERNAME or not TARGET_PASSWORD:
        print("[ERRO] Credenciais não encontradas. Configure o arquivo .env:")
        print("  TARGET_USERNAME=seu_usuario")
        print("  TARGET_PASSWORD=sua_senha")
        result.errors.append("Credenciais ausentes no .env")
        return result

    print(f"\n[CRAWLER] Iniciando navegação em {TARGET_URL}")
    print(f"[CRAWLER] Usuário: {TARGET_USERNAME}")
    print(f"[CRAWLER] Headless: {headless}")

    # Modo config-driven (YAML) — tenta antes do fluxo hardcoded
    crawler_config = _load_crawler_config(config_path)
    if crawler_config and "stages" in crawler_config:
        print("[CRAWLER] Modo: config-driven (crawler_config.yaml)")
        driver = _build_driver(headless=headless)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        try:
            for stage in crawler_config["stages"]:
                print(f"\n[ETAPA] {stage.get('name', '?')}...")
                _execute_config_stage(stage, driver, wait, result)
        finally:
            driver.quit()
            print("\n[CRAWLER] Navegador fechado.")
        print("\n" + result.summary())
        return result

    # Fallback: fluxo hardcoded
    print("[CRAWLER] Modo: fluxo hardcoded")
    driver = _build_driver(headless=headless)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    try:
        # ETAPA 1: Tela de Login
        print("\n[ETAPA 1] Tela de login...")
        driver.get(TARGET_URL)
        time.sleep(2)
        result.pages["01_login"] = _save_html(driver, "01_login")

        # ETAPA 2: Autenticação
        print("\n[ETAPA 2] Autenticando...")
        try:
            wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(TARGET_USERNAME)
            driver.find_element(By.ID, "password").send_keys(TARGET_PASSWORD)
            driver.find_element(By.ID, "loginBtn").click()
            print("  Login submetido.")
        except Exception as e:
            result.errors.append(f"ETAPA 2 - Login falhou: {e}")
            result.pages["02_login_error"] = _save_html(driver, "02_login_error")
            return result

        time.sleep(6)
        result.pages["02_post_login"] = _save_html(driver, "02_post_login")

        # ETAPA 3: Dashboard & Reports
        print("\n[ETAPA 3] Navegando para Dashboard & Reports...")
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(), 'Dashboard & Reports')]")
            )).click()
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "yui-navset-top")))
            time.sleep(2)
            result.pages["03_reports"] = _save_html(driver, "03_reports")
        except Exception as e:
            result.errors.append(f"ETAPA 3 - Dashboard & Reports: {e}")
            result.pages["03_reports_error"] = _save_html(driver, "03_reports_error")

        # ETAPA 4: Canned Reports
        print("\n[ETAPA 4] Clicando em Canned Reports...")
        try:
            canned = wait.until(EC.element_to_be_clickable((By.ID, "tab1")))
            driver.execute_script("arguments[0].click();", canned)
            wait.until(EC.presence_of_element_located((By.ID, "cannedReports")))
            time.sleep(3)
            result.pages["04_canned_reports"] = _save_html(driver, "04_canned_reports")
        except Exception as e:
            result.errors.append(f"ETAPA 4 - Canned Reports: {e}")
            result.pages["04_canned_reports_error"] = _save_html(driver, "04_canned_reports_error")

        # ETAPA 5: Botão Run
        print("\n[ETAPA 5] Localizando relatório Adherence Audit...")
        try:
            run_button_xpath = (
                "//tr[td/a[contains("
                "translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                "'abcdefghijklmnopqrstuvwxyz'),'adherence audit')]]"
                "//a[contains(text(), 'Run')]"
            )
            run_btn = wait.until(EC.element_to_be_clickable((By.XPATH, run_button_xpath)))
            driver.execute_script("arguments[0].click();", run_btn)
            time.sleep(10)
            result.pages["05_run_config"] = _save_html(driver, "05_run_config")
        except Exception as e:
            result.errors.append(f"ETAPA 5 - Botão Run: {e}")
            result.pages["05_run_error"] = _save_html(driver, "05_run_error")

        # ETAPA 6: Configuração do período
        print("\n[ETAPA 6] Configurando período...")
        try:
            wait.until(EC.presence_of_element_located((By.ID, "rdw_tf_interval")))
            result.pages["06_period_config"] = _save_html(driver, "06_period_config")
        except Exception as e:
            result.errors.append(f"ETAPA 6 - Configuração de período: {e}")
            result.pages["06_period_error"] = _save_html(driver, "06_period_error")

    except Exception as e:
        result.errors.append(f"Erro não tratado: {e}")
        try:
            result.pages["unexpected_error"] = _save_html(driver, "unexpected_error")
        except Exception:
            pass

    finally:
        driver.quit()
        print("\n[CRAWLER] Navegador fechado.")

    print("\n" + result.summary())
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Authenticated HTML Crawler")
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Abre janela do Chrome (desativa headless — útil para debug)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Caminho para crawler_config.yaml alternativo",
    )
    args = parser.parse_args()

    crawl(headless=not args.visible, config_path=args.config)