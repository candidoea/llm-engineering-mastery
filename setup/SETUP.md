# Setup do Ambiente

Este guia cobre a configuração do ambiente para acompanhar o curso.  
O curso usa **Cursor** como editor e **uv** como gerenciador de pacotes (substituiu o Anaconda na versão 2025).

---

## Pré-requisitos

- Python 3.11 ou superior
- Git
- Cursor (editor — [download](https://cursor.sh/))

---

## Instalação do `uv`

**Mac / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Reinicie o terminal após a instalação.

---

## Clonar e configurar o repositório

```bash
git clone https://github.com/SEU_USUARIO/llm-engineering-mastery.git
cd llm-engineering-mastery

# Cria o ambiente virtual e instala dependências
uv sync

# Configura as API keys
cp .env.example .env
# Abra o .env no editor e preencha com suas chaves
```

---

## Configurar o kernel no Cursor

1. Abra o Cursor na pasta `llm-engineering-mastery`
2. Abra qualquer notebook (ex: `week1/day1.ipynb`)
3. Clique em **"Select Kernel"** (canto superior direito)
4. Escolha **"Python Environments"**
5. Selecione a opção com estrela: `.venv (Python 3.x)`

---

## API Keys necessárias

| Semana | API | Onde obter |
|--------|-----|------------|
| Week 1+ | OpenAI | [platform.openai.com](https://platform.openai.com/) |
| Week 1+ | Anthropic | [console.anthropic.com](https://console.anthropic.com/) |
| Week 1+ | Google | [ai.google.dev](https://ai.google.dev/) |
| Week 3+ | HuggingFace | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) — **permissão WRITE** |

---

## Custo estimado de API

Ed Donner estima: "a few cents at a time", não mais que $2-3 no total.  
Week 7 pode ser ligeiramente mais caro (~$10 no Colab Pro, opcional).

Monitore em:
- [OpenAI Usage](https://platform.openai.com/usage)
- [Anthropic Cost](https://console.anthropic.com/settings/cost)

---

## Google Colab (Weeks 3, 6, 7)

Algumas aulas usam Colab para acessar GPU. Os links estão dentro de cada notebook diário.  
O plano gratuito é suficiente para a maioria das aulas.

---

## Atualizar o repositório durante o curso

Ed Donner atualiza o repo com frequência. Para puxar as atualizações do repositório original:

```bash
# Adicione o repo original como upstream (só na primeira vez)
git remote add upstream https://github.com/ed-donner/llm_engineering.git

# Para trazer atualizações do curso (sem sobrescrever suas notas)
git fetch upstream
git merge upstream/main --allow-unrelated-histories
```

---

## Problemas comuns

Ver o [FAQ oficial](https://edwarddonner.com/faq/) para os problemas mais comuns.
