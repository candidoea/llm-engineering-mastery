from pathlib import Path

ROOT = Path(__file__).parent

SCRAPERS_DIR = ROOT / "scrapers"
HTML_DIR = ROOT / "html"
REPORTS_DIR = ROOT / "reports"
OUTPUT_DIR = ROOT / "output"
PROMPTS_DIR = ROOT / "prompts"

# --- Ollama ---
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"

# Modelos disponíveis no seu Ollama (do menor para o maior):
# phi3          → 3.8B  — mais rápido em CPU, suficiente para análise de seletores
# llama3.2      → 3B    — bom equilíbrio velocidade/qualidade
# qwen2.5-coder:7b → 7B — melhor qualidade, mas lento em CPU puro
#
# Para tarefas de diagnóstico de seletores, phi3 ou llama3.2 são suficientes.
# Use qwen2.5-coder:7b apenas para geração do scraper corrigido.
OLLAMA_MODEL_FAST = "phi3"          # diagnóstico rápido
OLLAMA_MODEL_CODE = "qwen2.5-coder:7b"  # geração de código (fase 5)

# Timeout em segundos por requisição ao Ollama
# phi3 em CPU: ~60-120s para prompts médios
# qwen2.5-coder:7b em CPU: ~300-600s
OLLAMA_TIMEOUT = 180

# Limite de caracteres enviados ao LLM por fase
# Evita prompts que travam o modelo
MAX_PROMPT_CHARS = 4000

# Criar diretórios se não existirem
for directory in [HTML_DIR, REPORTS_DIR, OUTPUT_DIR]:
    directory.mkdir(exist_ok=True)

# =============================================================================
# Mapeamento seletor → etapa do fluxo (TASK-03)
#
# Pode ser definido manualmente OU gerado automaticamente via
# build_stage_map() com base nas URLs acessadas no scraper.
#
# Quando definido manualmente: linha → nome da etapa
# Quando gerado automaticamente: heurística por URL e ordem de acesso
# =============================================================================
SELECTOR_STAGE_MAP: dict[int, str] = {
    66: "01_login",
    67: "01_login",
    68: "01_login",
    77: "03_reports",
    81: "03_reports",
    88: "04_canned_reports",
    92: "04_canned_reports",
    103: "05_run_config",
    113: "05_run_config",
    125: "05_run_config",
    133: "06_period_config",
    150: "06_period_config",
    158: "06_period_config",
    171: "06_period_config",
}


def build_stage_map(
    selectors: list,
    stage_order: list[str],
) -> dict[int, str]:
    """
    Gera SELECTOR_STAGE_MAP automaticamente quando não definido manualmente.

    Heurística: divide os seletores em blocos proporcionais às etapas,
    respeitando a ordem de linha. Seletores no primeiro terço vão para
    as primeiras etapas, etc.

    Útil para scrapers novos onde o mapeamento ainda não foi definido.
    Para máxima precisão, defina SELECTOR_STAGE_MAP manualmente após
    a primeira execução.

    Args:
        selectors: lista de Selector extraídos do scraper
        stage_order: lista de nomes de etapas em ordem

    Returns:
        dict {linha: etapa}
    """
    if not selectors or not stage_order:
        return {}

    sorted_sels = sorted(selectors, key=lambda s: s.line)
    n = len(sorted_sels)
    stages = len(stage_order)
    block = max(1, n // stages)

    result = {}
    for i, sel in enumerate(sorted_sels):
        stage_idx = min(i // block, stages - 1)
        result[sel.line] = stage_order[stage_idx]

    return result

# Mapeamento etapa → arquivo HTML capturado pelo crawler
# Permite que o doctor saiba qual HTML usar para cada etapa
HTML_STAGE_ORDER = [
    "01_login",
    "02_post_login",
    "03_reports",
    "04_canned_reports",
    "05_run_config",
    "06_period_config",
]