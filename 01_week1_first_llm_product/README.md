# Semana 1 — Primeiro Produto LLM: Explorando Modelos de Fronteira

**Duração do curso:** 5h 44min  
**Foco do laboratório:** Entender como APIs de LLMs funcionam sob o capô antes de usá-las como caixa preta.

---

## Objetivos de Aprendizado

Ao final desta semana você deve ser capaz de:

- Chamar APIs de múltiplos provedores (OpenAI, Anthropic, Google) de forma programática
- Comparar modelos por capacidade, custo e latência com métricas objetivas
- Entender a estrutura de uma chamada de API (tokens, roles, system prompt, parâmetros de sampling)
- Construir um produto funcional simples que usa LLMs como componente

---

## Estrutura

```
01_week1_first_llm_product/
├── notebooks/
│   ├── 01_api_fundamentals.ipynb        # Anatomia de uma chamada de API
│   ├── 02_token_counting_and_cost.ipynb # Como tokens funcionam, estimativa de custo
│   ├── 03_sampling_parameters.ipynb     # Temperatura, top-p, top-k na prática
│   ├── 04_model_comparison.ipynb        # Benchmark entre modelos
│   └── 05_first_product.ipynb           # Produto integrador da semana
├── src/
│   ├── llm_client.py                    # Wrapper unificado multi-provedor
│   └── evaluator.py                     # Métricas de comparação
└── tests/
    ├── test_llm_client.py
    └── test_evaluator.py
```

---

## Conceitos de Suporte (Fundamentos)

Antes de explorar os notebooks desta semana, certifique-se de ter lido:
- `00_foundations/math_probability/04_sampling_strategies.ipynb` — entender temperatura e top-p requer probabilidade básica

---

## Notebooks

### `01_api_fundamentals.ipynb`
Disseção de uma chamada de API: o que é um token, como roles (system/user/assistant) estruturam o contexto, o que são stop sequences.

### `02_token_counting_and_cost.ipynb`
Como tokenizers funcionam (BPE), por que o mesmo texto gera contagens diferentes entre modelos, como estimar custo antes de fazer uma chamada.

### `03_sampling_parameters.ipynb`
Experimento comparativo: o mesmo prompt com temperatura 0, 0.5, 1.0, 2.0. Visualização da distribuição de probabilidade dos tokens.

### `04_model_comparison.ipynb`
Framework de avaliação: latência, custo por token, qualidade em tarefas específicas. Comparação entre GPT-4o, Claude Sonnet, Gemini Pro.

### `05_first_product.ipynb`
Produto integrador: assistente de análise de código com múltiplos modelos em paralelo, comparação de respostas, seleção automatizada.
