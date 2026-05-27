# Week 2 — Chatbot Multimodal: LLMs, Gradio UI e Agentes

**Seção do curso:** Seção 2 — 24 aulas, 3h 41min

## O que o curso cobre

- Interface de chat com Gradio (texto, imagem, áudio)
- Gerenciamento de histórico de conversa (context window)
- Tool use e function calling em profundidade
- Integração multimodal: processar imagens com Vision models
- Notificações push com Pushover
- Deploy de aplicação no HuggingFace Spaces

## Arquivos do curso

Notebooks `day1.ipynb` a `day5.ipynb` — cada dia constrói sobre o anterior.

## Minhas anotações e extensões

### Observações da semana

### Experimentos próprios

### Dúvidas para investigar

## Links úteis para esta semana

- [Gradio Docs](https://www.gradio.app/docs/)
- [HuggingFace Spaces](https://huggingface.co/spaces)
- [OpenAI Vision Guide](https://platform.openai.com/docs/guides/vision)
- [Pushover API](https://pushover.net/api)

## Conceito-chave: Context Window Management

Quando o histórico de conversa excede o limite de tokens, a estratégia importa:
- **Sliding window:** descarta as mensagens mais antigas
- **Summarization:** resume o histórico antes de descartar
- **RAG-based:** recupera o histórico relevante em vez de mantê-lo todo

Na semana 5 (RAG) voltaremos a isso com muito mais rigor.
