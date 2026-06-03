# Scraper Doctor — Tasks

Backlog organizado por versão. Cada task tem critério de aceite explícito.

---

## v0.3.0 — Em andamento

### TASK-01: Corrigir seletores de login do sistema alvo
**Prioridade:** Bloqueante — sem isso o crawler não avança da Etapa 2  
**Módulo:** `crawler.py`  
**O que fazer:**
1. Abrir `html/01_login.html` no browser
2. Identificar os IDs reais dos campos de usuário, senha e botão de submit
3. Atualizar as linhas 120-124 do `crawler.py` com os novos seletores
4. Rodar `uv run python crawler.py` isolado para validar

**Critério de aceite:** `[ETAPA 2] Autenticando... Login submetido.` aparece no log sem erro

---

### TASK-02: Adicionar campo `stage` em `Selector`
**Prioridade:** Alta  
**Módulo:** `extractor.py`  
**O que fazer:**
```python
# Antes
@dataclass
class Selector:
    strategy: str
    value: str
    line: int

# Depois
@dataclass
class Selector:
    strategy: str
    value: str
    line: int
    stage: str = "unknown"  # etapa do fluxo a que pertence
```

**Critério de aceite:** `summarize()` exibe a coluna `stage` no output

---

### TASK-03: Implementar `SELECTOR_STAGE_MAP` em `config.py`
**Prioridade:** Alta  
**Módulo:** `config.py`  
**O que fazer:**
```python
# Mapeamento linha do scraper → etapa do fluxo
SELECTOR_STAGE_MAP: dict[int, str] = {
    66: "login",   # input_username
    67: "login",   # input_password
    68: "login",   # input_login_submit
    77: "reports", # Dashboard & Reports
    81: "reports", # yui-navset-top
    88: "reports", # tab1
    92: "reports", # cannedReports
    103: "run",    # run_button_xpath
    113: "run",    # rdw_tf_interval
    125: "run",    # rw_run_btn
    133: "export", # rw_export_btn
    150: "export", # rr_output_format_CSV
    158: "export", # rr_output_format_apply
    171: "download", # pd_btn_download
}
```

**Critério de aceite:** `extract_from_file()` popula `Selector.stage` corretamente para cada linha

---

### TASK-04: Refatorar `comparator.py` para filtrar por etapa
**Prioridade:** Alta  
**Módulo:** `comparator.py`  
**O que fazer:**
- Adicionar parâmetro `stage: str | None` em `compare()`
- Quando `stage` fornecido, comparar apenas seletores daquela etapa
- Seletores de outras etapas: ignorar (não marcar como quebrados)

**Critério de aceite:** ao comparar `01_login.html` com `stage="login"`, apenas os 3 seletores de login são verificados; os 9 restantes não aparecem no relatório

---

### TASK-05: Criar `metrics.py`
**Prioridade:** Alta  
**Módulo:** `metrics.py` (novo)  
**O que fazer:**
```python
@dataclass
class RunMetrics:
    total_time_s: float = 0.0
    crawl_time_s: float = 0.0
    llm_time_s: float = 0.0
    tokens_prompt: int = 0
    tokens_completion: int = 0
    selectors_total: int = 0
    selectors_ok: int = 0
    selectors_broken: int = 0
    selectors_fixed: int = 0
    stages_completed: int = 0
    stages_failed: int = 0
    retries_total: int = 0

    @property
    def fix_rate_pct(self) -> float:
        if self.selectors_broken == 0:
            return 100.0
        return self.selectors_fixed / self.selectors_broken * 100

    def report(self) -> str:
        """Retorna relatório formatado dos KPIs."""
        ...
```

**Critério de aceite:** ao final de cada execução, o terminal exibe tabela de KPIs incluindo tokens e fix_rate_pct

---

### TASK-06: Capturar tokens do LLM em `llm_client.py`
**Prioridade:** Média  
**Módulo:** `llm_client.py`  
**O que fazer:**
- Modo streaming: Ollama retorna `usage` no chunk final — capturar
- Modo blocking: `response.usage.prompt_tokens` e `response.usage.completion_tokens`
- Retornar junto com o texto da resposta

**Critério de aceite:** `RunMetrics.tokens_prompt` e `tokens_completion` são preenchidos após cada chamada ao LLM

---

### TASK-07: Criar `engine.py` — motor sequencial
**Prioridade:** Alta  
**Módulo:** `engine.py` (novo)  
**O que fazer:**
Implementar o ciclo correto:
```
para cada etapa em [login, reports, run, export, download]:
    1. Crawler executa a etapa e salva o HTML
    2. Comparator verifica seletores DA ETAPA contra o HTML
    3. Se tudo OK: avança para próxima etapa
    4. Se quebrado:
       a. LLM diagnostica
       b. Aplica correção temporária nos seletores
       c. Crawler re-executa a etapa
       d. Se passou: avança
       e. Se não passou após MAX_RETRIES: registra falha e para
```

**Critério de aceite:** ao rodar com login quebrado, a ferramenta para na Etapa 2, diagnostica `input_username`, sugere correção, e não tenta as etapas 3-6

---

### TASK-08: Atualizar `architecture.md` e `statusspec.md` após v0.3.0
**Prioridade:** Baixa (fazer após as outras tasks)  
**Módulo:** `docs/`  
**Critério de aceite:** documentação reflete a arquitetura real implementada

---

## Backlog futuro (v0.4.0+)

| ID | Descrição | Versão |
|----|-----------|--------|
| TASK-09 | `agent.py`: executar scraper real e capturar traceback | v0.4.0 |
| TASK-10 | `agent.py`: screenshot no momento da falha | v0.4.0 |
| TASK-11 | `agent.py`: ciclo de correção com limite de iterações | v0.4.0 |
| TASK-12 | Generalizar crawler para qualquer site via YAML | v1.0.0 |
| TASK-13 | Suporte a Playwright além de Selenium | v1.0.0 |
| TASK-14 | Interface Gradio para uso sem CLI | v1.0.0 |