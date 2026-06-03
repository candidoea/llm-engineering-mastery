# Scraper Doctor — Plan

## Versão atual: v0.2.0 (em produção)

### O que foi entregue
- Extração de seletores via AST
- Crawler autenticado no sistema alvo (Selenium)
- Comparação estática por BeautifulSoup
- Diagnóstico LLM com streaming (phi3)
- Geração de scraper corrigido (qwen2.5-coder:7b)
- CLI com `--crawl`, `--visible`, `--fix`

### Limitações conhecidas
- Diagnóstico não é sequencial por etapa
- Todos os seletores são comparados contra todos os HTMLs
- KPIs limitados a tempo de execução
- Login falha (ID `input_username` mudou — exemplo real de uso)

---

## v0.3.0 — Diagnóstico Sequencial e KPIs (próxima versão)

### Objetivo
Implementar o ciclo correto: executar etapa → falhar → diagnosticar só essa etapa → corrigir → reexecutar → avançar.

### Entregas

**1. Mapeamento seletor → etapa (`extractor.py` + `config.py`)**
- Novo campo `stage: str` em `Selector`
- Mapeamento definido em `SELECTOR_STAGE_MAP` no `config.py`
- Comparação estática usa apenas seletores da etapa atual

**2. Motor de execução sequencial (`engine.py` — novo módulo)**
- Substitui o loop simples do `doctor.py`
- Ciclo por etapa: executar → verificar → diagnosticar → corrigir → reexecutar
- Limite de retentativas por etapa (`MAX_RETRIES_PER_STAGE = 3`)
- Para e reporta se etapa não converge após retentativas

**3. KPIs (`metrics.py` — novo módulo)**

| KPI | Fonte | Significado |
|-----|-------|------------|
| `total_time_s` | `time.perf_counter()` | Tempo total de execução |
| `crawl_time_s` | Crawler | Tempo gasto em navegação |
| `llm_time_s` | LLM client | Tempo gasto em inferência |
| `tokens_prompt` | API response | Tokens enviados ao LLM |
| `tokens_completion` | API response | Tokens gerados pelo LLM |
| `selectors_total` | Extractor | Total de seletores no scraper |
| `selectors_ok` | Comparator | Seletores válidos na comparação estática |
| `selectors_broken` | Comparator | Seletores quebrados detectados |
| `selectors_fixed` | Engine | Seletores corrigidos com sucesso |
| `fix_rate_pct` | Calculado | `selectors_fixed / selectors_broken * 100` |
| `stages_completed` | Engine | Etapas concluídas com sucesso |
| `stages_failed` | Engine | Etapas que não convergiram |
| `retries_total` | Engine | Total de retentativas realizadas |

**4. Correção do login (`crawler.py`)**
- Inspecionar `html/01_login.html` para identificar novos IDs
- Atualizar seletores de login no `crawler.py`

---

## v0.4.0 — Scraper Doctor Agent

### Objetivo
Fechar o ciclo completo: o agente executa o scraper real, captura o erro e itera até corrigir.

### Entregas

**`agent.py` — novo módulo**
- Executa `original_scraper.py` em subprocess com timeout
- Captura: traceback, screenshot, `page_source` no momento da falha
- Envia ao LLM com contexto completo
- Aplica patch no scraper
- Reexecuta e repete até sucesso ou `MAX_AGENT_ITERATIONS`

**Critério de parada**
- Sucesso: scraper executa sem exceção
- Falha: `MAX_AGENT_ITERATIONS` atingido (default: 5)
- Divergência: LLM sugere a mesma correção duas vezes sem progresso

---

## v1.0.0 — Generalização

### Objetivo
Remover dependência de qualquer sistema específico. A ferramenta deve funcionar para qualquer scraper Selenium.

### Entregas
- Configuração de fluxo via YAML (etapas, seletores, URLs)
- Suporte a Playwright além de Selenium
- Suporte a `requests` + BeautifulSoup para scrapers não-interativos
- Interface web simples (Gradio) para uso sem CLI