# Semana 2 — Chatbot Multimodal com Gradio e Agentes

**Duração do curso:** 3h 41min

## Objetivos

- Construir interface de chat funcional com Gradio
- Integrar input de imagem + texto (multimodal)
- Implementar um agente simples com tool use
- Gerenciar histórico de conversa (context window management)

## Estrutura

```
notebooks/
  01_gradio_basics.ipynb           # Interface de chat do zero
  02_multimodal_input.ipynb        # Processamento de imagem + texto
  03_tool_use_fundamentals.ipynb   # Function calling / tool use
  04_conversation_management.ipynb # Histórico, truncation, resumo
src/
  chatbot.py    # Lógica do chatbot
  tools.py      # Ferramentas disponíveis para o agente
tests/
  test_chatbot.py
  test_tools.py
```

## Conceito-chave desta semana

Context window management: como decidir o que manter e descartar quando o histórico excede o limite de tokens. Três estratégias: sliding window, summarization, retrieval-augmented.
