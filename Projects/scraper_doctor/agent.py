"""
agent.py — Scraper Doctor Agent Mode (Fase 6)

Ciclo autônomo:
    1. Recebe o scraper_fixed.py gerado pelo doctor
    2. Injeta perfil de teste (SCRAPER_ENV=test) via variáveis de ambiente
    3. Executa o scraper como subprocess com timeout
    4. Captura: sucesso / traceback / timeout
    5. [falha] → envia traceback ao LLM → gera patch → reexecuta
    6. [sucesso] → entrega scraper_fixed.py limpo (credenciais originais intactas)
    7. Repete até sucesso ou MAX_ITERATIONS

Princípio: o scraper_fixed.py NUNCA é modificado com credenciais de teste.
O perfil de teste é injetado apenas via variáveis de ambiente no subprocess.
"""

import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR, REPORTS_DIR, OLLAMA_MODEL_CODE
from llm_client import ask

MAX_ITERATIONS = 3
TEST_TIMEOUT_SECONDS = 120  # máximo por execução de teste


@dataclass
class AgentIteration:
    """Resultado de uma iteração do agent."""
    iteration: int
    success: bool
    exit_code: int | None = None
    traceback: str = ""
    patch_applied: str = ""
    duration_s: float = 0.0


@dataclass
class AgentResult:
    """Resultado completo do ciclo do agent."""
    success: bool
    iterations: list[AgentIteration] = field(default_factory=list)
    final_scraper: Path | None = None
    total_time_s: float = 0.0

    def summary(self) -> str:
        status = "✅ SUCESSO" if self.success else "❌ FALHOU"
        lines = [
            f"\n{'=' * 60}",
            f"AGENT MODE — {status}",
            f"{'=' * 60}",
            f"Iterações: {len(self.iterations)}/{MAX_ITERATIONS}",
            f"Tempo total: {self.total_time_s:.1f}s",
        ]
        if self.final_scraper:
            lines.append(f"Scraper final: {self.final_scraper.name}")
        for it in self.iterations:
            status_it = "✓" if it.success else "✗"
            lines.append(
                f"  [{status_it}] Iteração {it.iteration}: "
                f"{it.duration_s:.1f}s | exit={it.exit_code}"
            )
            if it.traceback:
                # Mostra apenas a última linha do traceback (erro principal)
                last_line = [l for l in it.traceback.splitlines() if l.strip()]
                if last_line:
                    lines.append(f"       Erro: {last_line[-1][:80]}")
        return "\n".join(lines)


def _build_test_env(original_scraper_path: Path) -> dict[str, str]:
    """
    Constrói as variáveis de ambiente para execução em modo teste.

    Sobrescreve caminhos de rede e servidor com equivalentes locais.
    Credenciais do .env local são usadas para autenticação.
    O código fonte do scraper não é modificado.
    """
    env = os.environ.copy()

    # Perfil de execução
    env["SCRAPER_ENV"] = "test"

    # Diretório de download local (pasta temp dentro do projeto)
    local_download = OUTPUT_DIR / "test_downloads"
    local_download.mkdir(exist_ok=True)
    env["TEST_DOWNLOAD_DIR"] = str(local_download)

    # Timeout reduzido para testes
    env["SCRAPER_TIMEOUT"] = "30"

    return env


def _inject_test_profile(scraper_code: str) -> str:
    """
    Injeta suporte a perfil de teste no código do scraper.

    O bloco injetado:
    - Inclui seus próprios imports (Path, os) para ser autossuficiente
    - Substitui DOWNLOAD_DIR pelo diretório local de teste
    - Sobrescreve USER_EMAIL e USER_PASSWORD com credenciais do .env
    - Não modifica o código original fora do bloco

    Inserido APÓS todos os imports para garantir que as variáveis
    do scraper original (USER_EMAIL, USER_PASSWORD) já existam.
    """
    test_profile_block = """
# === SCRAPER DOCTOR: TEST PROFILE ===
import os as _os
from pathlib import Path as _Path
if _os.environ.get("SCRAPER_ENV") == "test":
    _dotenv_ok = False
    try:
        from dotenv import load_dotenv as _lde
        _lde()
        _dotenv_ok = True
    except ImportError:
        pass
    # Sobrescreve caminhos de rede com diretório local
    DOWNLOAD_DIR = _os.environ.get(
        "TEST_DOWNLOAD_DIR",
        str(_Path(__file__).parent.parent / "output" / "test_downloads")
    )
    _Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    # Sobrescreve credenciais com as do .env local (sempre atualizadas)
    USER_EMAIL = _os.environ.get("TARGET_USERNAME", USER_EMAIL)
    USER_PASSWORD = _os.environ.get("TARGET_PASSWORD", USER_PASSWORD)
    print(f"[TEST MODE] SCRAPER_ENV=test")
    print(f"[TEST MODE] Download dir: {DOWNLOAD_DIR}")
    print(f"[TEST MODE] Usuario: {USER_EMAIL}")
    print(f"[TEST MODE] .env carregado: {_dotenv_ok}")
# =====================================
"""

    lines = scraper_code.splitlines()

    # Estratégia: encontra a ÚLTIMA ocorrência de USER_EMAIL ou USER_PASSWORD
    # e insere o bloco logo após. Isso garante que ambas as variáveis existam.
    last_credential_line = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("USER_EMAIL") or stripped.startswith("USER_PASSWORD"):
            last_credential_line = i

    if last_credential_line >= 0:
        # Insere após a última linha de credencial
        insert_at = last_credential_line + 1
    else:
        # Fallback: insere após o bloco de imports
        insert_at = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")) or stripped == "":
                insert_at = i + 1
            elif stripped and not stripped.startswith("#") and insert_at > 0:
                break

    lines.insert(insert_at, test_profile_block)
    return "\n".join(lines)


def _execute_scraper(
    scraper_path: Path,
    env: dict[str, str],
    timeout: int = TEST_TIMEOUT_SECONDS,
) -> tuple[bool, int, str]:
    """
    Executa o scraper como subprocess com timeout.

    Returns:
        (success, exit_code, output/traceback)
    """
    print(f"  [AGENT] Executando: {scraper_path.name}")
    print(f"  [AGENT] Timeout: {timeout}s")

    start = time.perf_counter()

    try:
        result = subprocess.run(
            [sys.executable, str(scraper_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            cwd=str(scraper_path.parent.parent),  # raiz do scraper_doctor
        )

        duration = time.perf_counter() - start
        output = result.stdout + result.stderr
        success = result.returncode == 0

        if success:
            print(f"  [AGENT] ✅ Sucesso em {duration:.1f}s")
        else:
            print(f"  [AGENT] ✗ Falhou (exit={result.returncode}) em {duration:.1f}s")
            # Extrai as últimas 10 linhas do output (onde fica o traceback)
            lines = [l for l in output.splitlines() if l.strip()]
            traceback_snippet = "\n".join(lines[-10:]) if lines else "Sem output"
            print(f"  [AGENT] Erro:\n    {traceback_snippet.replace(chr(10), chr(10) + '    ')}")

        return success, result.returncode, output

    except subprocess.TimeoutExpired:
        duration = time.perf_counter() - start
        print(f"  [AGENT] ⏱ Timeout após {duration:.1f}s")
        return False, -1, f"TimeoutExpired após {timeout}s"

    except Exception as e:
        print(f"  [AGENT] Erro ao executar: {e}")
        return False, -2, str(e)


def _extract_traceback(output: str) -> str:
    """Extrai apenas o traceback relevante do output do scraper."""
    lines = output.splitlines()
    traceback_start = -1

    for i, line in enumerate(lines):
        if "Traceback (most recent call last)" in line:
            traceback_start = i

    if traceback_start >= 0:
        return "\n".join(lines[traceback_start:])

    # Se não tem traceback formal, retorna as últimas 15 linhas
    return "\n".join(lines[-15:]) if lines else output


def _generate_patch(
    scraper_code: str,
    traceback: str,
    iteration: int,
) -> str:
    """
    Envia o traceback ao LLM e recebe um patch para o scraper.
    Usa qwen2.5-coder:7b para maior precisão em código.
    """
    system = (
        "Você é um especialista em Python e Selenium. "
        "Analise o erro e corrija APENAS a linha ou função que causou o problema. "
        "Retorne APENAS o código Python corrigido, sem explicações, sem markdown."
    )

    prompt = f"""O script Selenium falhou com o seguinte erro (iteração {iteration}):

TRACEBACK:
{traceback}

CÓDIGO DO SCRAPER (primeiras 100 linhas):
{chr(10).join(scraper_code.splitlines()[:100])}

Corrija apenas o ponto de falha. Preserve toda a lógica restante.
Retorne o código Python completo corrigido."""

    print(f"  [AGENT] Consultando LLM para patch (iteração {iteration})...")
    return ask(prompt, system=system, model=OLLAMA_MODEL_CODE, stream=True)


def run_agent(
    scraper_fixed_path: str | Path,
    max_iterations: int = MAX_ITERATIONS,
) -> AgentResult:
    """
    Executa o ciclo autônomo do Agent mode.

    Args:
        scraper_fixed_path: caminho para o scraper_fixed.py gerado pelo doctor
        max_iterations: número máximo de tentativas antes de desistir

    Returns:
        AgentResult com histórico de iterações e scraper final
    """
    start_total = time.perf_counter()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    fixed_path = Path(scraper_fixed_path)
    if not fixed_path.exists():
        print(f"[AGENT] Arquivo não encontrado: {fixed_path}")
        return AgentResult(success=False)

    print("\n" + "=" * 60)
    print("SCRAPER DOCTOR — AGENT MODE")
    print("=" * 60)
    print(f"Scraper: {fixed_path.name}")
    print(f"Máximo de iterações: {max_iterations}")

    # Lê o código original — nunca será modificado diretamente
    original_code = fixed_path.read_text(encoding="utf-8", errors="replace")

    # Cria versão de teste com perfil injetado
    test_code = _inject_test_profile(original_code)
    test_path = OUTPUT_DIR / f"scraper_test_{ts}.py"
    test_path.write_text(test_code, encoding="utf-8")
    print(f"Script de teste: {test_path.name}")

    # Prepara ambiente de teste
    test_env = _build_test_env(fixed_path)

    result = AgentResult(success=False)
    current_code = test_code

    for iteration in range(1, max_iterations + 1):
        print(f"\n{'─' * 60}")
        print(f"ITERAÇÃO {iteration}/{max_iterations}")
        print(f"{'─' * 60}")

        # Salva versão atual do teste
        test_path.write_text(current_code, encoding="utf-8")

        iter_start = time.perf_counter()
        success, exit_code, output = _execute_scraper(
            test_path, test_env, timeout=TEST_TIMEOUT_SECONDS
        )
        iter_duration = time.perf_counter() - iter_start

        traceback = _extract_traceback(output) if not success else ""

        agent_iter = AgentIteration(
            iteration=iteration,
            success=success,
            exit_code=exit_code,
            traceback=traceback,
            duration_s=iter_duration,
        )
        result.iterations.append(agent_iter)

        if success:
            result.success = True
            result.final_scraper = fixed_path  # entrega o original (sem perfil de teste)
            print(f"\n[AGENT] ✅ Scraper validado na iteração {iteration}.")
            print(f"[AGENT] Scraper entregue: {fixed_path.name}")
            print("[AGENT] Credenciais originais preservadas — nenhuma modificação no scraper_fixed.py")
            break

        if iteration < max_iterations:
            # Gera patch via LLM
            patch = _generate_patch(current_code, traceback, iteration)

            # Remove markdown que o LLM insere (```python ... ```)
            clean = patch.strip()
            if clean.startswith("```"):
                clean = "\n".join(clean.split("\n")[1:])
            if "```" in clean:
                clean = clean[:clean.rfind("```")].rstrip()
            clean = clean.strip()

            # Valida sintaxe — se inválido, mantém código anterior
            try:
                compile(clean, "<patch>", "exec")
                patch = clean
                print("  [AGENT] Patch com sintaxe válida.")
            except SyntaxError as e:
                print(f"  [AGENT] ⚠️  Patch inválido ({e}) — mantendo código anterior.")
                patch = current_code

            # Guarda o patch para auditoria
            patch_path = REPORTS_DIR / f"agent_patch_{ts}_iter{iteration}.py"
            patch_path.write_text(patch, encoding="utf-8")

            agent_iter.patch_applied = str(patch_path)
            current_code = patch
            print(f"  [AGENT] Patch salvo: {patch_path.name}")
        else:
            print(f"\n[AGENT] ❌ Limite de {max_iterations} iterações atingido sem sucesso.")
            print("[AGENT] Revise manualmente os patches em reports/agent_patch_*.py")

    # Limpa arquivo de teste
    if test_path.exists():
        test_path.unlink()
        print(f"[AGENT] Arquivo de teste removido: {test_path.name}")

    result.total_time_s = time.perf_counter() - start_total
    print(result.summary())

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scraper Doctor — Agent Mode")
    parser.add_argument(
        "scraper_fixed",
        help="Caminho para o scraper_fixed.py gerado pelo doctor",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=MAX_ITERATIONS,
        help=f"Máximo de iterações (default: {MAX_ITERATIONS})",
    )
    args = parser.parse_args()

    run_agent(
        scraper_fixed_path=args.scraper_fixed,
        max_iterations=args.iterations,
    )