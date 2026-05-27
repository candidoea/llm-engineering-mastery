# 99 — Capstone: Sistema LLM End-to-End

Este é o projeto integrador do repositório. Combina todos os módulos anteriores em um sistema coeso que demonstra capacidade de engenharia end-to-end.

## Objetivo

Construir um sistema de Q&A especializado que:

1. Ingere documentos técnicos (PDFs, markdown)
2. Cria um índice RAG com embeddings densos
3. Usa um modelo open-source fine-tunado (semana 7) como gerador
4. Expõe uma interface de chat (semana 2)
5. Inclui um agente que pode buscar informações complementares na web (semana 8)
6. Avalia respostas com métricas objetivas (semana 4)

## O que este projeto demonstra para o portfólio

- Capacidade de integrar componentes de diferentes paradigmas
- Decisões de arquitetura justificadas (por que esse chunker? por que esse retriever?)
- Avaliação objetiva, não apenas "parece que funciona"
- Código de produção: testes, logging, tratamento de erros, configuração via environment

## Estrutura

```
99_capstone/
├── notebooks/
│   └── 00_capstone_design.ipynb    # Decisões de arquitetura documentadas
├── src/
│   ├── ingestion/     # Pipeline de ingestão de documentos
│   ├── retrieval/     # Sistema RAG
│   ├── generation/    # Wrapper do modelo fine-tunado
│   ├── agents/        # Agente com tool use
│   ├── evaluation/    # Métricas automáticas
│   └── app.py         # Entrypoint Gradio
└── README.md
```

## Critério de conclusão

O projeto está completo quando:
- [ ] Sistema responde perguntas técnicas com citação da fonte
- [ ] Latência de resposta < 10s em hardware de consumidor
- [ ] Testes de integração passando
- [ ] README explica cada decisão de arquitetura
- [ ] Demo gravado e linkado aqui
