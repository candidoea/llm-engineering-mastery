# Scraper Doctor — StatusSpec

**Versão:** 0.2.0  
**Data:** 2026-06-02  
**Status:** Em desenvolvimento ativo

---

## 1. Estado Atual do Projeto

### O que funciona
- Extração de seletores via AST (12 seletores extraídos corretamente do `original_scraper.py`)
- Navegação autenticada com Selenium (abre o sistema alvo, captura HTML da tela de login)
- Comparação estática via BeautifulSoup
- Diagnóstico via LLM com streaming (phi3)
- Geração de relatórios em `reports/`

### O que não funciona ainda
- **Login falha:** `input_username` não encontrado — o site alterou o ID do campo
- **Diagnóstico sequencial ausente:** todos os seletores são comparados contra todos os HTMLs, independente da etapa a que pertencem
- **Sem parada e correção por etapa:** a ferramenta não para quando encontra um erro, não corrige, não testa e não avança
- **KPIs incompletos:** apenas tempo de execução é registrado

### Problema central identificado (2026-06-02)
O fluxo atual é: capturar todos os HTMLs → diagnosticar tudo → reportar. O fluxo correto é: tentar etapa → falhou → diagnosticar só essa etapa → corrigir seletor → tentar novamente → avançar. Diagnóstico sem correção iterativa tem valor limitado para o caso de uso real.

---

## 2. Decisões Arquiteturais

### DA-01: AST em vez de Regex para extração de seletores
**Decisão:** usar `ast.NodeVisitor` para extrair seletores.  
**Motivo:** regex captura apenas padrões fixos. AST captura qualquer estilo de aspas, chamadas aninhadas e seletores em variáveis.  
**Trade-off:** AST falha em seletores construídos por concatenação de strings em runtime — esses são marcados como `<variável>` e tratados como não verificáveis estaticamente.

### DA-02: Comparação estática antes do LLM
**Decisão:** BeautifulSoup verifica cada seletor antes de chamar o LLM.  
**Motivo:** LLM em CPU é lento (60-600s por prompt). Comparação estática é instantânea e resolve IDs renomeados, classes removidas e CSS selectors alterados sem custo de inferência.  
**Trade-off:** BeautifulSoup não suporta XPath nativamente; seletores XPATH são encaminhados ao LLM via heurística.

### DA-03: Dois modelos por fase
**Decisão:** `phi3` para diagnóstico (Fase 4), `qwen2.5-coder:7b` para geração de código (Fase 5).  
**Motivo:** diagnóstico requer raciocínio sobre texto; geração de código requer precisão sintática. Phi3 é 2x mais rápido em CPU para a primeira tarefa.  
**Trade-off:** qualidade do diagnóstico do phi3 é inferior ao qwen2.5-coder. Aceitável porque o diagnóstico é validado pela comparação estática antes.

### DA-04: Prompt cirúrgico (não envia código inteiro)
**Decisão:** o LLM recebe apenas os seletores quebrados e um snippet HTML com elementos interativos.  
**Motivo:** prompt de 8.316 chars (código inteiro) levava ao travamento do modelo em CPU. Prompt cirúrgico reduz para ~2.000-3.000 chars.  
**Trade-off:** o LLM perde contexto sobre a lógica de navegação. Mitigado pelo fato de que o diagnóstico estático já identificou o que quebrou.

### DA-05: Diagnóstico sequencial com parada por etapa (PLANEJADO — v0.3.0)
**Decisão:** cada etapa do crawler testa seus seletores, para ao detectar falha, tenta correção e só avança após sucesso.  
**Motivo:** diagnosticar etapas posteriores sem ter passado pela anterior gera falsos positivos — seletores de páginas internas aparecem como "quebrados" na tela de login.  
**Trade-off:** tempo de execução maior por iteração; necessário limite de retentativas por etapa.

### DA-06: Mapeamento explícito seletor → etapa (PLANEJADO — v0.3.0)
**Decisão:** cada seletor é anotado com a etapa do fluxo a que pertence.  
**Motivo:** sem esse mapeamento, a comparação estática não sabe quais seletores verificar em qual HTML.  
**Implementação:** novo campo `stage` em `Selector`; mapeamento definido em `config.py`.

---

## 3. Glossário de Domínio

| Termo | Definição |
|-------|-----------|
| **Scraper** | Script Python que automatiza navegação web via Selenium para extrair dados ou executar ações |
| **Seletor** | Estratégia de localização de elemento HTML (By.ID, By.XPATH, By.CSS_SELECTOR, etc.) |
| **Etapa** | Passo discreto do fluxo de navegação do scraper (login, relatórios, run, export, download) |
| **HTML de etapa** | HTML capturado pelo crawler imediatamente antes de interagir com os elementos daquela etapa |
| **Seletor quebrado** | Seletor que não encontra correspondência no HTML atual da etapa a que pertence |
| **Diagnóstico estático** | Comparação de seletores com HTML via BeautifulSoup, sem LLM |
| **Diagnóstico LLM** | Análise de seletores quebrados via modelo de linguagem local (Ollama) |
| **Prompt cirúrgico** | Prompt que contém apenas os seletores quebrados e snippet HTML relevante, não o código completo |
| **Correção iterativa** | Ciclo: executar etapa → falhar → diagnosticar → corrigir seletor → reexecutar → avançar |
| **KPI** | Key Performance Indicator — métrica de desempenho da ferramenta |
| **Token** | Unidade de processamento do LLM; afeta custo e tempo de inferência |
| **Taxa de correção** | Proporção de seletores corrigidos com sucesso pelo LLM em relação aos seletores quebrados identificados |

---

## 4. Padrões de Código

### Nomenclatura
- Módulos: `snake_case` (ex: `llm_client.py`, `comparator.py`)
- Classes: `PascalCase` (ex: `ScraperProfile`, `ComparisonReport`)
- Funções públicas: `snake_case` (ex: `extract_from_file`, `diagnose_with_llm`)
- Funções privadas: prefixo `_` + `snake_case` (ex: `_build_driver`, `_save_html`)
- Constantes: `UPPER_SNAKE_CASE` (ex: `TARGET_URL`, `OLLAMA_TIMEOUT`)
- Variáveis de ambiente: prefixo do serviço + `UPPER_SNAKE_CASE` (ex: `TARGET_USERNAME`, `CHROME_DRIVER_PATH`)

### Estrutura de módulo
Cada módulo segue a ordem:
1. Docstring de módulo (propósito, decisão arquitetural referenciada)
2. Imports stdlib
3. Imports third-party
4. Imports internos
5. Constantes
6. Dataclasses/modelos
7. Funções privadas (`_`)
8. Funções públicas
9. `if __name__ == "__main__"` (quando aplicável)

### Docstrings
```python
def funcao(param: tipo) -> tipo_retorno:
    """
    Uma linha descrevendo o que faz.

    Referência arquitetural quando relevante (ex: DA-02).

    Args:
        param: descrição

    Returns:
        descrição do retorno

    Raises:
        ValueError: quando e por quê
    """
```

### Tratamento de erros
- Erros de etapa do crawler: capturados, registrados em `CrawlResult.errors`, não interrompem o processo
- Erros de LLM: timeout explícito via `OLLAMA_TIMEOUT`; falha registrada no relatório
- Erros fatais (credenciais ausentes, arquivo não encontrado): `sys.exit(1)` com mensagem clara

### Credenciais
- Nunca hardcoded
- Sempre via `.env` + `python-dotenv`
- `.env` no `.gitignore`
- `.env.example` versionado com placeholders

### Outputs
- `html/`: HTMLs capturados (não versionado — `.gitignore`)
- `reports/`: relatórios de diagnóstico (não versionado)
- `output/`: scrapers corrigidos (não versionado)
- Nomenclatura: `{tipo}_{YYYYMMDD_HHMMSS}_{etapa}.{ext}`