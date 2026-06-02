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

HTML_STAGE_ORDER = [
    "01_login",
    "02_post_login",
    "03_reports",
    "04_canned_reports",
    "05_run_config",
    "06_period_config",
]