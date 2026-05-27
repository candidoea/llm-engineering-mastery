# LLM Engineering — Mastery Repository

Fork e extensão pessoal do repositório oficial do curso
**[AI Engineer Core Track: LLM Engineering, RAG, QLoRA, Agents](https://www.udemy.com/course/llm-engineering-master-ai-and-large-language-models/)** — Ed Donner

Repositório original: [ed-donner/llm_engineering](https://github.com/ed-donner/llm_engineering)

---

## Como este repositório se organiza

```
llm-engineering-mastery/
│
├── week1/          ← Conteúdo do curso: Explorando modelos de fronteira
├── week2/          ← Conteúdo do curso: Chatbot multimodal, Gradio, Agentes
├── week3/          ← Conteúdo do curso: Open-source GenAI com HuggingFace
├── week4/          ← Conteúdo do curso: Avaliação de modelos, code gen
├── week5/          ← Conteúdo do curso: RAG e embeddings vetoriais
├── week6/          ← Conteúdo do curso: ML → DL → Fine-tuning de fronteira
├── week7/          ← Conteúdo do curso: Fine-tune open-source vs frontier
├── week8/          ← Conteúdo do curso: Sistema multi-agente autônomo
│
├── guides/         ← Guias do curso (git, APIs, Colab, etc.)
├── setup/          ← Instruções de ambiente
├── extras/         ← Conteúdo extra e experimentos do curso
├── community-contributions/  ← Soluções da comunidade
│
└── 00_deep_dive/   ← EXTENSÃO PESSOAL: fundamentos matemáticos from scratch
    ├── math_linear_algebra/
    ├── math_calculus/
    ├── math_probability/
    ├── math_information_theory/
    └── architecture_transformers/
```

**Separação clara:** as pastas `week1/` a `week8/` seguem o curso do Ed Donner. A pasta `00_deep_dive/` é conteúdo adicional meu, com implementações matemáticas que o curso não cobre, para aprofundar o entendimento dos fundamentos.

---

## Setup (novo — usando `uv`)

O curso usa `uv` como gerenciador de pacotes e **Cursor** como editor.

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/llm-engineering-mastery.git
cd llm-engineering-mastery

# 2. Instale o uv se não tiver
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Crie o ambiente e instale dependências
uv sync

# 4. Configure as API keys
cp .env.example .env
# Edite o .env com suas chaves
```

Instruções detalhadas de setup por plataforma em [setup/SETUP.md](setup/SETUP.md).

---

## Progresso semanal

| Semana | Tema | Status |
|--------|------|--------|
| Week 1 | Explorando modelos de fronteira — primeiros produtos LLM | 🔄 |
| Week 2 | Chatbot multimodal com Gradio e Agentes | ⬜ |
| Week 3 | GenAI open-source com HuggingFace no Google Colab | ⬜ |
| Week 4 | Avaliação de modelos para code gen e negócios | ⬜ |
| Week 5 | RAG avançado com embeddings vetoriais | ⬜ |
| Week 6 | De ML tradicional a DL a fine-tuning de fronteira | ⬜ |
| Week 7 | Fine-tune open-source para competir com modelo frontier | ⬜ |
| Week 8 | Sistema multi-agente autônomo | ⬜ |

---

## Extensão pessoal — `00_deep_dive/`

O curso é focado em aplicação. Esta pasta contém o que o curso não cobre: a matemática e a mecânica interna de cada componente.

| Módulo | Conteúdo |
|--------|----------|
| `math_linear_algebra/` | Vetores, produto interno, SVD — a base de embeddings e attention |
| `math_calculus/` | Gradientes, backprop manual, autograd from scratch |
| `math_probability/` | Distribuições, MLE, sampling (temperatura, top-p, top-k) |
| `math_information_theory/` | Entropia, cross-entropy loss, KL-divergence, perplexidade |
| `architecture_transformers/` | Atenção from scratch, positional encoding, decoder-only GPT nano |

---

## Recursos do curso

- [Página de recursos do Ed Donner](https://edwarddonner.com/2024/11/13/llm-engineering-resources/)
- [FAQ do curso](https://edwarddonner.com/faq/)
- [Slides do curso](https://drive.google.com/drive/folders/1GMXbdgkqnZfCRcIdoUVBBB-hxeN4Lo06)
- [Repositório original](https://github.com/ed-donner/llm_engineering)

---

## Contribuindo

Se quiser contribuir com soluções dos exercícios do curso, consulte o [guia de contribuição](guides/CONTRIBUTING.md) e submeta um Pull Request para `community-contributions/`.
