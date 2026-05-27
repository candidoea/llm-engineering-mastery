# Week 4 — Avaliação de Modelos para Code Gen e Negócios

**Seção do curso:** Seção 4 — 21 aulas, 3h 9min

## O que o curso cobre

- Frameworks de avaliação: como medir qualidade de LLMs objetivamente
- LLM-as-a-Judge: usar um modelo para avaliar outro
- Benchmarks para code generation (HumanEval, MBPP)
- Avaliação para casos de uso de negócios
- Comparação de custo-benefício entre modelos para tarefas específicas
- Structured outputs: forçar saída JSON/schema

## Arquivos do curso

Notebooks `day1.ipynb` a `day5.ipynb`.

## Minhas anotações e extensões

### Observações da semana

### Experimentos próprios

### Dúvidas para investigar

## Links úteis para esta semana

- [OpenAI Evals](https://github.com/openai/evals)
- [HumanEval Benchmark](https://github.com/openai/human-eval)
- [LMSYS Chatbot Arena](https://lmsys.org/blog/2023-05-03-arena/)
- [Vellum Leaderboard](https://www.vellum.ai/llm-leaderboard)

## Conceito-chave: LLM-as-a-Judge

Em vez de depender de comparações humanas (caro e lento), usamos um LLM de alta qualidade como árbitro.

Limitações a considerar:
- **Bias de posição:** o modelo tende a preferir a primeira resposta
- **Bias de verbosidade:** respostas mais longas são frequentemente preferidas
- **Auto-preferência:** modelos às vezes preferem outputs semelhantes aos seus próprios

A semana 4 mostra como mitigar esses problemas na prática.
