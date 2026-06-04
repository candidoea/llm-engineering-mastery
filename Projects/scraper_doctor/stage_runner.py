"""
stage_runner.py — Geração e execução de scripts mínimos por etapa.

Responsabilidade: dado um conjunto de seletores de uma etapa e seus
substitutos candidatos, gera um script Python mínimo que testa apenas
aquela etapa e o executa para validar.

Critério de sucesso: script executa sem exceção Selenium +
pelo menos um elemento da próxima etapa é encontrado no HTML resultante.
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv

from config import OUTPUT_DIR, REPORTS_DIR

load_dotenv(Path(__file__).parent / ".env")

TARGET_URL = os.environ.get("TARGET_URL", "")
TARGET_USERNAME = os.environ.get("TARGET_USERNAME", "")
TARGET_PASSWORD = os.environ.get("TARGET_PASSWORD", "")

MAX_STAGE_RETRIES = 3
STAGE_TIMEOUT = 60  # segundos por execução de script mínimo


def generate_minimal_script(
    stage_name: str,
    navigation_code: str,
    selectors_with_fixes: dict[str, str],
    next_stage_selector: tuple[str, str] | None = None,
    requires_login: bool = False,
    login_selectors: dict | None = None,
) -> str:
    """
    Gera um script Python mínimo para testar uma etapa específica.

    Args:
        stage_name: nome da etapa
        navigation_code: código de navegação extraído do scraper original
        selectors_with_fixes: {seletor_original: substituto_candidato}
        next_stage_selector: (strategy, value) assertion da próxima etapa
        requires_login: se True, inclui bloco de login antes da etapa
        login_selectors: seletores de login já validados
            {username_id, password_id, submit_id}

    Returns:
        Código Python do script mínimo
    """
    # Monta as substituições inline no código de navegação
    fixed_code = navigation_code
    for original, candidate in selectors_with_fixes.items():
        fixed_code = fixed_code.replace(
            f'"{original}"', f'"{candidate}"'
        ).replace(
            f"'{original}'", f"'{candidate}'"
        )

    # Bloco de login para etapas que requerem autenticação
    if requires_login and login_selectors:
        un_id = login_selectors.get("username_id", "username")
        pw_id = login_selectors.get("password_id", "password")
        sb_id = login_selectors.get("submit_id", "loginBtn")
        login_block = f"""
    # Login necessário para esta etapa
    driver.get(TARGET_URL)
    import time as _time
    _time.sleep(2)
    wait.until(EC.presence_of_element_located((By.ID, "{un_id}"))).send_keys(TARGET_USERNAME)
    driver.find_element(By.ID, "{pw_id}").send_keys(TARGET_PASSWORD)
    driver.find_element(By.ID, "{sb_id}").click()
    _time.sleep(5)
    print("[STAGE] Login realizado")
"""
    else:
        login_block = ""

    # Assertion da próxima etapa
    if next_stage_selector:
        strategy, value = next_stage_selector
        assertion = f"""
    # Assertion: verifica elemento da próxima etapa
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    _wait = WebDriverWait(driver, 15)
    _wait.until(EC.presence_of_element_located((By.{strategy}, "{value}")))
    print("[STAGE] Assertion OK: elemento da próxima etapa encontrado")
"""
    else:
        assertion = '    print("[STAGE] Sem assertion de próxima etapa")\n'

    script = f'''"""Script mínimo gerado pelo Scraper Doctor — Etapa: {stage_name}"""
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

TARGET_URL = os.environ.get("TARGET_URL", "{TARGET_URL}")
TARGET_USERNAME = os.environ.get("TARGET_USERNAME", "{TARGET_USERNAME}")
TARGET_PASSWORD = os.environ.get("TARGET_PASSWORD", "{TARGET_PASSWORD}")

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)

try:
{login_block}
{_indent(fixed_code)}
{assertion}
    print("[STAGE] {stage_name}: SUCESSO")

except Exception as e:
    print(f"[STAGE] {stage_name}: FALHOU — {{e}}")
    raise

finally:
    driver.quit()
'''
    return script


def _indent(code: str, spaces: int = 4) -> str:
    """Indenta código para dentro do bloco try."""
    lines = code.strip().splitlines()
    return "\n".join(f"{' ' * spaces}{line}" for line in lines)


def run_minimal_script(
    script_code: str,
    stage_name: str,
    iteration: int = 1,
) -> tuple[bool, str]:
    """
    Executa um script mínimo como subprocess.

    Args:
        script_code: código Python do script mínimo
        stage_name: nome da etapa (para logs)
        iteration: número da tentativa atual

    Returns:
        (sucesso, output/traceback)
    """
    # Salva script em arquivo temporário
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        prefix=f"stage_{stage_name}_iter{iteration}_",
        dir=str(OUTPUT_DIR),
        delete=False,
        encoding="utf-8",
    )
    tmp.write(script_code)
    tmp.close()
    tmp_path = Path(tmp.name)

    env = os.environ.copy()
    env["TARGET_URL"] = TARGET_URL
    env["TARGET_USERNAME"] = TARGET_USERNAME
    env["TARGET_PASSWORD"] = TARGET_PASSWORD

    try:
        result = subprocess.run(
            [sys.executable, str(tmp_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=STAGE_TIMEOUT,
            env=env,
        )

        output = result.stdout + result.stderr
        success = result.returncode == 0

        if success:
            print(f"  [RUNNER] ✅ {stage_name} passou (iter {iteration})")
        else:
            lines = [l for l in output.splitlines() if l.strip()]
            last_error = lines[-1] if lines else "sem output"
            print(f"  [RUNNER] ✗ {stage_name} falhou: {last_error[:100]}")

        return success, output

    except subprocess.TimeoutExpired:
        print(f"  [RUNNER] ⏱ {stage_name} timeout após {STAGE_TIMEOUT}s")
        return False, f"TimeoutExpired após {STAGE_TIMEOUT}s"

    finally:
        # Remove script temporário
        tmp_path.unlink(missing_ok=True)


def extract_traceback(output: str) -> str:
    """Extrai traceback do output."""
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if "Traceback (most recent call last)" in line:
            return "\n".join(lines[i:])
    return "\n".join(lines[-10:]) if lines else output


def validate_stage(
    stage_name: str,
    navigation_code: str,
    selectors_with_fixes: dict[str, str],
    next_stage_selector: tuple[str, str] | None = None,
    max_retries: int = MAX_STAGE_RETRIES,
    requires_login: bool = False,
    login_selectors: dict | None = None,
) -> tuple[bool, dict[str, str]]:
    """
    Valida os substitutos de seletores de uma etapa via execução real.

    Itera até MAX_STAGE_RETRIES tentativas. Em cada falha, retorna
    os substitutos que falharam para que o LLM possa sugerir alternativas.

    Args:
        stage_name: nome da etapa
        navigation_code: código de navegação da etapa
        selectors_with_fixes: {seletor_original: candidato_atual}
        next_stage_selector: assertion da próxima etapa
        max_retries: máximo de tentativas

    Returns:
        (sucesso, substitutos_validados)
    """
    print(f"\n  [RUNNER] Validando etapa: {stage_name}")
    current_fixes = dict(selectors_with_fixes)

    for attempt in range(1, max_retries + 1):
        script = generate_minimal_script(
            stage_name=stage_name,
            navigation_code=navigation_code,
            selectors_with_fixes=current_fixes,
            next_stage_selector=next_stage_selector,
            requires_login=requires_login,
            login_selectors=login_selectors,
        )

        success, output = run_minimal_script(script, stage_name, attempt)

        if success:
            return True, current_fixes

        if attempt < max_retries:
            traceback = extract_traceback(output)
            print(f"  [RUNNER] Tentativa {attempt}/{max_retries} falhou. Aguardando ajuste...")
            # Retorna para o caller decidir se aciona LLM
            return False, current_fixes

    return False, current_fixes