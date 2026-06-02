# Scraper Doctor

Diagnóstico e autocorreção automática de scrapers Selenium usando análise estática e LLM local via Ollama.

**Origem:** projeto derivado da Week 1 do curso [LLM Engineering (Ed Donner)](https://www.udemy.com/course/llm-engineering-master-ai-and-large-language-models/), onde o exercício era resumir uma página web com Ollama. A ideia foi estender isso para diagnosticar scrapers quebrados por mudanças no site alvo.

---

## O problema que resolve

Um scraper Selenium funcionava. O site alvo mudou o HTML — IDs, XPaths, estrutura do DOM. O scraper quebrou. Em vez de depurar manualmente, o Scraper Doctor:

1. Extrai todos os seletores do scraper via AST do Python
2. Navega no site autenticado com Selenium e captura o HTML de cada etapa do fluxo
3. Compara os seletores com o HTML atual — por etapa, sem falsos positivos
4. Sugere substitutos automaticamente via heurística de similaridade
5. Aciona o LLM apenas para seletores sem substituto automático
6. Gera o `scraper_fixed.py` com exatamente as substituições necessárias

---

## Pré-requisitos

- Python 3.11+
- [uv](https://astral.sh/uv) — gerenciador de pacotes
- [Ollama](https://ollama.com/) — runtime de LLM local
- Google Chrome instalado (o Selenium Manager baixa o ChromeDriver automaticamente)

### Instalação do Ollama

**Windows:**
1. Acesse [ollama.com/download](https://ollama.com/download) e baixe o instalador
2. Execute o instalador e siga as instruções
3. Após instalar, baixe os modelos necessários:

```powershell
ollama pull phi3
ollama pull qwen2.5-coder:7b
```

4. Para verificar se está funcionando:

```powershell
ollama list
```

> O Ollama precisa estar rodando durante o uso do Scraper Doctor. Se fechar o terminal do Ollama, execute `ollama serve` em um terminal separado antes de rodar o doctor.

---

## Setup

```powershell
# 1. Clone ou baixe o projeto
cd scraper_doctor

# 2. Instale o uv (se não tiver)
# Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 3. Instale as dependências
uv sync

# 4. Configure as credenciais
copy .env.example .env
# Abra o .env e preencha com suas credenciais
```

### Configuração do `.env`

```
TARGET_URL=https://login.seu-sistema.com/
TARGET_USERNAME=seu_usuario
TARGET_PASSWORD=sua_senha
```

---

## Uso

### Modo principal — crawl autenticado (recomendado)

Navega no site, captura o HTML de cada etapa e gera o scraper corrigido:

```powershell
python doctor.py scrapers/original_scraper.py --crawl --fix
```

Com janela do Chrome visível (útil para acompanhar a navegação):

```powershell
python doctor.py scrapers/original_scraper.py --crawl --visible --fix
```

Só diagnóstico, sem gerar scraper corrigido:

```powershell
python doctor.py scrapers/original_scraper.py --crawl
```

### Modo alternativo — HTML local

Se você já tem o HTML salvo da página onde o scraper falha:

```powershell
python doctor.py scrapers/original_scraper.py --html html/pagina.html --fix
```

### Modo alternativo — URL pública

Para páginas que não requerem autenticação:

```powershell
python doctor.py scrapers/original_scraper.py --url https://site.com/pagina
```

---

## Como funciona — fluxo resumido

```
scraper.py (com seletores quebrados)
    ↓
[FASE 1] Extrai seletores via AST — captura By.ID, By.XPATH, By.CLASS_NAME,
         find_element posicional, calls aninhados, seletores em variáveis
    ↓
[FASE 2] Crawler navega no site com Selenium — login autenticado,
         captura HTML de cada etapa do fluxo
    ↓
[FASE 3] Comparação estática por etapa — cada seletor comparado
         apenas contra o HTML da sua etapa (sem falsos positivos)
         Heurística: substring, núcleo sem prefixo, semântica, tipo de elemento
    ↓
    ├── Substituto encontrado → aplica diretamente (sem LLM)
    └── Sem substituto → envia ao LLM (phi3) com prompt cirúrgico
    ↓
[FASE 5] Gera scraper_fixed.py — cópia exata do original
         com apenas as substituições identificadas aplicadas
```

---

## Modelos Ollama

| Fase | Modelo | Uso |
|------|--------|-----|
| Diagnóstico (Fase 4) | `phi3` | Seletores sem substituto automático |
| Correção complexa (Fase 5) | `qwen2.5-coder:7b` | XPath e CSS complexos |

Configure em `config.py`:
```python
OLLAMA_MODEL_FAST = "phi3"
OLLAMA_MODEL_CODE = "qwen2.5-coder:7b"
```

> Em CPU puro, o `phi3` leva 60-300s por chamada. O `qwen2.5-coder:7b` pode levar 5-10 minutos. Por isso o LLM só é acionado quando a análise estática não consegue encontrar o substituto.

---

## Adaptando para outro site

O `crawler.py` atual está configurado para o fluxo de 6 etapas de um sistema específico. Para usar com outro site:

1. Edite `crawler.py` — adapte as etapas de navegação
2. Edite `config.py` — atualize o `SELECTOR_STAGE_MAP` com os números de linha do seu scraper e as etapas correspondentes
3. Atualize o `.env` com as credenciais do novo site

---

## Estrutura do projeto

```
scraper_doctor/
├── doctor.py         ← Orquestrador principal e CLI
├── extractor.py      ← Fase 1: extração via AST
├── crawler.py        ← Fase 2: navegação autenticada com Selenium
├── comparator.py     ← Fase 3: comparação estática e heurísticas
├── llm_client.py     ← Fases 4 e 5: interface com Ollama
├── metrics.py        ← KPIs de execução
├── config.py         ← Configurações e mapeamento seletor→etapa
├── pyproject.toml    ← Dependências (uv)
├── .env.example      ← Template de credenciais
├── docs/
│   ├── architecture.md  ← Arquitetura detalhada
│   ├── plan.md          ← Roadmap de versões
│   ├── statusspec.md    ← Decisões arquiteturais e glossário
│   └── tasks.md         ← Backlog de tarefas
├── scrapers/         ← Scrapers a diagnosticar (input)
├── html/             ← HTMLs capturados (não versionado)
├── reports/          ← Relatórios gerados (não versionado)
└── output/           ← Scrapers corrigidos (não versionado)
```

---

## Saídas geradas

| Arquivo | Localização | Conteúdo |
|---------|------------|----------|
| `static_report_*.txt` | `reports/` | Seletores OK e quebrados por etapa |
| `diagnosis_*.txt` | `reports/` | Diagnóstico do LLM para seletores sem substituto |
| `kpis_*.json` | `reports/` | Métricas de execução (tempo, tokens, taxa de correção) |
| `scraper_fixed_*.py` | `output/` | Scraper original com substituições aplicadas |

---

## Próxima evolução: Scraper Doctor Agent

```
Executar scraper → capturar traceback + screenshot + page_source
    ↓ Enviar ao LLM → gerar patch → testar → repetir até funcionar
```