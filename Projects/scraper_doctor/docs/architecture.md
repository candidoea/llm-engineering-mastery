# Scraper Doctor — Arquitetura

**Versão:** 0.3.0  
**Data:** 2026-06-02

---

## Visão Geral

Ferramenta de diagnóstico e autocorreção de scrapers Selenium. Usa LLM local (Ollama) como **último recurso** — a análise estática com heurísticas de similaridade resolve a maioria dos casos sem custo de inferência.

Princípio central: o `scraper_fixed.py` gerado é uma cópia exata do scraper original com **apenas** as substituições identificadas aplicadas. Nada mais é alterado.

---

## Estrutura de Diretórios

```
scraper_doctor/
│
├── doctor.py               ← Orquestrador principal e CLI
├── extractor.py            ← Fase 1: extração de seletores via AST
├── crawler.py              ← Fase 2: navegação autenticada com Selenium
├── comparator.py           ← Fase 3: comparação estática e heurísticas
├── llm_client.py           ← Fases 4 e 5: interface com Ollama
├── metrics.py              ← KPIs de execução
├── config.py               ← Configurações e SELECTOR_STAGE_MAP
├── pyproject.toml          ← Dependências (uv)
├── .env.example            ← Template de credenciais
│
├── docs/
│   ├── architecture.md     ← Este documento
│   ├── plan.md             ← Roadmap de versões
│   ├── statusspec.md       ← Decisões arquiteturais e glossário
│   └── tasks.md            ← Backlog de tarefas
│
├── scrapers/               ← Scrapers a diagnosticar (input)
├── html/                   ← HTMLs capturados (não versionado)
├── reports/                ← Relatórios gerados (não versionado)
├── output/                 ← Scrapers corrigidos (não versionado)
└── samples/                ← Exemplos para testes
```

---

## Fluxo de Execução

```
                    scraper.py
                        │
                        ▼
            ┌───────────────────────────┐
            │  FASE 1 — extractor.py    │
            │  AST do Python            │
            │                           │
            │  Captura:                 │
            │  · find_element(By.X, v)  │  ← args posicionais
            │  · wait.until((By.X, v))  │  ← tupla aninhada
            │  · By.ID, XPATH, CLASS    │
            │  · Seletores em variáveis │
            │  · URLs e ações           │
            │                           │
            │  Anota stage por linha    │
            │  via SELECTOR_STAGE_MAP   │
            └──────────┬────────────────┘
                       │ ScraperProfile (seletores + stage)
                       ▼
            ┌───────────────────────────┐
            │  FASE 2 — crawler.py      │
            │  Selenium autenticado     │
            │                           │
            │  Etapas capturadas:       │
            │  01_login                 │
            │  02_post_login            │
            │  03_reports               │
            │  04_canned_reports        │
            │  05_run_config            │
            │  06_period_config         │
            │                           │
            │  Salva html/*.html        │
            └──────────┬────────────────┘
                       │ CrawlResult {etapa: html_path}
                       ▼
            ┌───────────────────────────┐
            │  FASE 3 — comparator.py   │
            │  Por etapa (sem falsos    │
            │  positivos):              │
            │                           │
            │  Heurísticas de score:    │
            │  +100 correspondência     │
            │        exata              │
            │  +80  núcleo sem prefixo  │
            │       (input_X → X)       │
            │  +60  substring           │
            │  +50  tipo correto        │
            │       (submit button)     │
            │  +30  prefixo comum >50%  │
            │  +10  sobreposição        │
            │       semântica           │
            └──────────┬────────────────┘
                       │
           ┌───────────┴───────────────┐
           │                           │
    [Substituto automático]    [Sem substituto]
           │                           │
    Aplica diretamente          FASE 4 — llm_client.py
    (LLM não chamado)           Ollama phi3
                                Prompt cirúrgico:
                                · Só seletores sem substituto
                                · Snippet HTML relevante
                                · Resposta em JSON estruturado
                                · Guardião: valida que seletor
                                  original existe no código
                                       │
                               reports/diagnosis_*.txt
                                       │
                              [--fix passado?]
                                       │ sim
                                       ▼
                            FASE 5 — fix_with_llm
                            Aplica substituições:
                            · Só onde seletor existe no código
                            · Preserva tudo mais
                                       │
                               output/scraper_fixed_*.py
```

---

## Responsabilidade de Cada Módulo

| Módulo | Responsabilidade | Dependências |
|--------|-----------------|-------------|
| `doctor.py` | Orquestração das 5 fases, CLI, diagnóstico por etapa | Todos |
| `extractor.py` | Extração via `ast.NodeVisitor`, anotação de stage | Stdlib |
| `crawler.py` | Login e navegação autenticada, captura de HTML por etapa | `selenium`, `dotenv` |
| `comparator.py` | Comparação estática, heurísticas de score, busca semântica | `beautifulsoup4` |
| `llm_client.py` | Prompts Ollama, streaming, retry, guardião de substituição | `openai`, `config` |
| `metrics.py` | Coleta e exibição de KPIs de execução | Stdlib |
| `config.py` | Paths, modelos, timeouts, `SELECTOR_STAGE_MAP` | `pathlib` |

---

## Decisões de Design

### DA-01: AST em vez de Regex
Regex captura padrões fixos. AST captura qualquer padrão: aspas simples/duplas, chamadas aninhadas, args posicionais separados (`find_element(By.ID, "x")`), seletores em variáveis.

### DA-02: Comparação Estática Antes do LLM
BeautifulSoup é instantâneo. LLM em CPU leva 60-600s. O comparador com heurísticas de score resolve a maioria dos casos sem custo de inferência.

### DA-03: Diagnóstico por Etapa (v0.3.0)
Cada seletor é comparado apenas contra o HTML da sua etapa (`SELECTOR_STAGE_MAP`). Elimina falsos positivos — seletores de páginas internas não aparecem como quebrados no HTML de login.

### DA-04: Heurística de Score com Priorização por Tipo
O candidato correto vence pelo score mais alto. Bônus para elementos do tipo correto (`type=submit` para seletores de submit). Extração do núcleo sem prefixo (`input_username` → `username`).

### DA-05: Guardião de Substituição
Antes de aplicar qualquer substituição, verifica se o seletor original existe no código fonte. Impede que o LLM invente seletores que não estão no scraper.

### DA-06: Dois Modelos por Fase
`phi3` (3.8B) para diagnóstico: rápido, suficiente. `qwen2.5-coder:7b` para geração de código complexo: mais preciso sintaticamente.

### DA-07: Credenciais em .env
Nunca hardcoded. Lidas via `python-dotenv`. `.env` no `.gitignore`. `.env.example` versionado com placeholders genéricos.

---

## Configuração: SELECTOR_STAGE_MAP

Mapeamento de linha do scraper → etapa do fluxo. Deve ser atualizado quando o scraper mudar de estrutura:

```python
# config.py
SELECTOR_STAGE_MAP: dict[int, str] = {
    66: "01_login",           # input_username
    67: "01_login",           # input_password
    68: "01_login",           # input_login_submit
    77: "03_reports",         # Dashboard & Reports
    81: "03_reports",         # yui-navset-top
    88: "04_canned_reports",  # tab1
    ...
}
```

---

## KPIs Coletados

| KPI | Descrição |
|-----|-----------|
| `total_time_s` | Tempo total de execução |
| `crawl_time_s` | Tempo gasto em navegação Selenium |
| `llm_time_s` | Tempo gasto em inferência LLM |
| `llm_pct_of_total` | % do tempo em LLM |
| `llm_calls` | Número de chamadas ao Ollama |
| `tokens_prompt/completion` | Tokens enviados e gerados |
| `selectors_total/ok/broken/fixed` | Contagem de seletores |
| `fix_rate_pct` | Taxa de correção |
| `stages_attempted/completed/failed` | Progresso por etapa |

---

## Uso via CLI

```powershell
# Modo principal — crawl autenticado + correção
python doctor.py scrapers/original_scraper.py --crawl --visible --fix

# Só diagnóstico (sem gerar scraper corrigido)
python doctor.py scrapers/original_scraper.py --crawl --visible

# Com HTML local já capturado
python doctor.py scrapers/original_scraper.py --html html/03_reports.html --fix
```

---

## Evolução Planejada

Ver `plan.md` para o roadmap completo.

**v0.4.0 — Scraper Doctor Agent:**
```
Executar scraper → capturar traceback + screenshot + page_source
    ↓ LLM gera patch → testar → repetir até funcionar
```