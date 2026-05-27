# Week 8 — Sistema Multi-Agente Autônomo

**Seção do curso:** Seção 8 — 21/22 aulas, 3h 4min

## O que o curso cobre

- Arquitetura de agentes: ReAct, planejamento, memória
- Multi-agent frameworks: orquestração de múltiplos agentes especializados
- Tool use avançado: agentes que usam ferramentas reais (busca, código, APIs)
- Autonomous workflows: pipelines que operam sem intervenção humana
- Human-in-the-loop: quando e como inserir aprovação humana
- Projeto final: sistema multi-agente para resolver problema comercial complexo

## Arquivos do curso

Notebooks `day1.ipynb` a `day5.ipynb` — projeto integrador final.

## Minhas anotações e extensões

### Observações da semana

### Experimentos próprios

### Dúvidas para investigar

## Links úteis para esta semana

- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- Paper: [ReAct (Yao et al., 2022)](https://arxiv.org/abs/2210.03629)
- Paper: [Toolformer (Schick et al., 2023)](https://arxiv.org/abs/2302.04761)

## Conceito-chave: o que diferencia um agente de um chatbot

Um chatbot responde. Um agente age.

A distinção operacional:
- **Chatbot:** input → output (uma chamada ao modelo)
- **Agente:** input → planejar → executar ferramentas → observar → replanejar → ... → output

O loop de raciocínio e ação (ReAct) é o padrão dominante. Esta semana mostra como coordenar múltiplos agentes especializados operando em paralelo ou em sequência.

## Projeto final do curso

O sistema construído nesta semana integra tudo:
- RAG (week 5) para recuperar contexto
- Modelos fine-tunados (weeks 6-7) como componentes especializados
- Tool use (week 2) para interagir com APIs externas
- Avaliação (week 4) para medir a qualidade do sistema
