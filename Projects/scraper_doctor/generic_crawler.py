"""
generic_crawler.py — Crawler genérico que reproduz o fluxo do script original.

Não conhece nenhum site específico.
Lê o fluxo extraído pelo flow_extractor e o executa com Selenium,
substituindo credenciais pelas do .env e capturando HTML por etapa.

Critério de captura: HTML é salvo após cada driver.get() e após
blocos de ações que incluem cliques significativos.
"""

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from config import HTML_DIR
from flow_extractor import FlowAction, NavigationStage, extract_flow

load_dotenv(Path(__file__).parent / ".env")

TARGET_URL = os.environ.get("TARGET_URL", "")
TARGET_USERNAME = os.environ.get("TARGET_USERNAME", "")
TARGET_PASSWORD = os.environ.get("TARGET_PASSWORD", "")


@dataclass
class CrawlResult:
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
                lines.append(f"  {e.splitlines()[0][:120]}")
        return "\n".join(lines)


def _build_driver(headless: bool = True):
    from selenium import webdriver
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def _resolve_value(action: FlowAction) -> str:
    """
    Resolve o valor de uma ação substituindo variáveis de credencial
    pelas credenciais do .env.
    """
    if action.is_credential:
        # Detecta se é usuário ou senha pelo nome da variável capturada
        var = action.value or ""
        var_upper = var.upper()
        if "EMAIL" in var_upper or "USER" in var_upper or "USUARIO" in var_upper:
            return TARGET_USERNAME
        if "PASS" in var_upper or "SENHA" in var_upper or "PASSWORD" in var_upper:
            return TARGET_PASSWORD

    return action.value or ""


def _save_html(driver, name: str) -> Path:
    path = HTML_DIR / f"{name}.html"
    path.write_text(driver.page_source, encoding="utf-8")
    size = len(driver.page_source)
    print(f"  [HTML] Salvo: {path.name} ({size:,} chars)")
    return path


def _execute_action(
    action: FlowAction,
    driver,
    wait,
    result: CrawlResult,
    stage_name: str,
) -> bool:
    """
    Executa uma ação individual.
    Retorna True se bem-sucedida, False se falhou.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select

    STRATEGY_MAP = {
        "ID": By.ID,
        "XPATH": By.XPATH,
        "CLASS_NAME": By.CLASS_NAME,
        "CSS_SELECTOR": By.CSS_SELECTOR,
        "NAME": By.NAME,
    }

    try:
        if action.kind == "get":
            # Usa TARGET_URL do .env se a URL do script for diferente
            url = TARGET_URL if TARGET_URL else action.value
            driver.get(url)

        elif action.kind == "wait":
            time.sleep(float(action.value or 2))

        elif action.kind == "wait_for" and action.selector:
            strategy_name, sel_value = action.selector
            if sel_value.startswith("<"):  # variável não resolvida
                return True  # ignora silenciosamente
            strategy = STRATEGY_MAP.get(strategy_name, By.ID)
            wait.until(EC.presence_of_element_located((strategy, sel_value)))

        elif action.kind == "send_keys" and action.selector:
            strategy_name, sel_value = action.selector
            if sel_value.startswith("<"):
                return True
            strategy = STRATEGY_MAP.get(strategy_name, By.ID)
            value = _resolve_value(action)
            wait.until(
                EC.presence_of_element_located((strategy, sel_value))
            ).send_keys(value)

        elif action.kind == "click" and action.selector:
            strategy_name, sel_value = action.selector
            if sel_value.startswith("<"):
                return True
            strategy = STRATEGY_MAP.get(strategy_name, By.ID)
            wait.until(
                EC.element_to_be_clickable((strategy, sel_value))
            ).click()

        elif action.kind == "click_js" and action.selector:
            strategy_name, sel_value = action.selector
            if sel_value.startswith("<"):
                return True
            strategy = STRATEGY_MAP.get(strategy_name, By.ID)
            element = wait.until(
                EC.element_to_be_clickable((strategy, sel_value))
            )
            driver.execute_script("arguments[0].click();", element)

        elif action.kind == "select" and action.selector:
            strategy_name, sel_value = action.selector
            if sel_value.startswith("<"):
                return True
            strategy = STRATEGY_MAP.get(strategy_name, By.ID)
            element = wait.until(
                EC.presence_of_element_located((strategy, sel_value))
            )
            Select(element).select_by_value(action.value or "")

        return True

    except Exception as e:
        result.errors.append(f"{stage_name} L{action.line} {action.kind}: {e}")
        return False


def crawl_from_script(
    scraper_path: str | Path,
    headless: bool = True,
    capture_every_n_clicks: int = 3,
) -> CrawlResult:
    """
    Reproduz o fluxo do script original e captura HTML por etapa.

    Genérico — funciona para qualquer scraper Selenium.
    Credenciais substituídas pelas do .env automaticamente.

    Args:
        scraper_path: caminho para o script original
        headless: modo headless do Chrome
        capture_every_n_clicks: captura HTML a cada N cliques significativos

    Returns:
        CrawlResult com HTMLs capturados por etapa
    """
    from selenium.webdriver.support.ui import WebDriverWait

    result = CrawlResult()

    if not TARGET_USERNAME or not TARGET_PASSWORD:
        result.errors.append("Credenciais ausentes no .env (TARGET_USERNAME, TARGET_PASSWORD)")
        return result

    stages = extract_flow(scraper_path)
    if not stages:
        result.errors.append("Nenhuma ação de navegação encontrada no script")
        return result

    print(f"\n[CRAWLER] Modo: genérico ({len(stages)} etapa(s) no script)")
    print(f"[CRAWLER] Usuário: {TARGET_USERNAME}")
    print(f"[CRAWLER] Headless: {headless}")

    driver = _build_driver(headless=headless)
    wait = WebDriverWait(driver, 30)

    try:
        for stage in stages:
            stage_name = stage.name
            print(f"\n[ETAPA] {stage_name}" + (f" → {stage.url}" if stage.url else ""))

            click_count = 0
            stage_failed = False

            for action in stage.actions:
                success = _execute_action(action, driver, wait, result, stage_name)

                if not success:
                    stage_failed = True
                    # Captura HTML do erro e continua
                    error_name = f"{stage_name}_error"
                    if error_name not in result.pages:
                        result.pages[error_name] = _save_html(driver, error_name)
                    break

                # Conta cliques para decidir quando capturar HTML
                if action.kind in ("click", "click_js"):
                    click_count += 1

            # Captura HTML após cada etapa (com get ou após cliques)
            if stage.url or click_count >= 1:
                if stage_name not in result.pages:
                    # Pequena espera para JS carregar
                    time.sleep(1.5)
                    result.pages[stage_name] = _save_html(driver, stage_name)

            # Verifica aviso institucional (popup genérico com Acknowledge)
            try:
                ack = driver.find_elements(
                    __import__("selenium.webdriver.common.by", fromlist=["By"]).By.XPATH,
                    "//input[@value='Acknowledge' or @value='OK' or @value='Accept' or @value='Close']"
                )
                if ack:
                    ack[0].click()
                    time.sleep(2)
                    print("  [OK] Popup institucional fechado automaticamente")
                    # Re-captura HTML limpo após fechar popup
                    result.pages[stage_name] = _save_html(driver, stage_name)
            except Exception:
                pass

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