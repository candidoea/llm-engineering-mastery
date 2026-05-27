# Guia de Contribuição e Workflow

Este documento define o workflow de desenvolvimento do repositório, incluindo convenções de branch, commit e notebook.

---

## Workflow de Branch

```
main          ← produção (apenas merges de develop via PR)
develop       ← integração (base para features)
feature/...   ← desenvolvimento de módulo ou notebook
fix/...       ← correção de bug
```

Fluxo padrão:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/00-linear-algebra-svd
# ... desenvolver ...
git push origin feature/00-linear-algebra-svd
# Abrir PR para develop
```

---

## Convenção de Commits (Conventional Commits)

Formato: `<tipo>(<escopo>): <descrição>`

| Tipo | Quando usar |
|------|-------------|
| `feat` | Novo notebook, nova função, nova funcionalidade |
| `fix` | Correção de bug em implementação |
| `docs` | Mudança apenas em documentação |
| `test` | Adição ou correção de testes |
| `refactor` | Refatoração sem mudança de comportamento |
| `chore` | Configuração, CI, dependências |

Exemplos:
```
feat(foundations): add SVD implementation from scratch
test(week1): add unit tests for LLMClient
fix(rag): fix chunking off-by-one in token counting
docs(week5): add mathematical derivation for cosine similarity
```

---

## Convenção de Notebooks

Cada notebook deve seguir esta estrutura obrigatória:

1. **Célula 1 — Markdown:** título `# Título`, metadados (módulo, pré-requisitos, tempo)
2. **Célula 2 — Markdown:** motivação (por que este conceito importa para LLMs)
3. **Célula 3+ — Código/Markdown:** derivação matemática intercalada com implementação
4. **Última célula — Markdown:** resumo e link para o próximo notebook

Regra de commit para notebooks: **sempre limpe os outputs** antes de commitar:
```bash
jupyter nbconvert --clear-output --inplace notebooks/*.ipynb
```

---

## Estrutura de Testes

- Cada arquivo `src/modulo.py` tem correspondente `tests/test_modulo.py`
- Testes não dependem de API keys (use mocks)
- Testes de integração com APIs ficam em `tests/integration/` e rodam manualmente
- Coverage mínimo esperado: 80% para código de biblioteca

---

## Padrão de Docstring

```python
def funcao(param: tipo) -> tipo_retorno:
    """
    Uma linha descrevendo o que faz.

    Contexto matemático ou de LLM quando relevante.
    Ex: referência à equação do paper original.

    Args:
        param: descrição do parâmetro

    Returns:
        descrição do retorno

    Raises:
        ValueError: quando e por quê
    """
```
