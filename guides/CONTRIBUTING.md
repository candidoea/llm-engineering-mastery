# Guia de Contribuição

Seguindo o modelo do repositório original do Ed Donner: se você desenvolveu uma solução interessante para os exercícios do curso, pode publicá-la aqui para referência futura.

---

## Como contribuir

1. Crie um branch: `git checkout -b feature/week3-exercise-solucao`
2. Adicione seu arquivo em `community-contributions/weekN/`
3. Nomeie de forma descritiva: `week3_hf_pipeline_custom.ipynb`
4. Faça commit com mensagem clara: `feat(week3): solução alternativa usando pipeline customizado`
5. Abra um Pull Request para `main`

---

## Convenção de commits

```
feat(weekN):   nova solução ou notebook
fix(weekN):    correção de bug
docs:          atualização de README ou anotações
chore:         configuração, dependências
```

---

## O que não commitar

- Arquivo `.env` com API keys
- Notebooks com outputs salvos (limpe antes: `Edit > Clear All Outputs`)
- Modelos baixados (`.bin`, `.safetensors`, `.gguf`)
- Dados de treinamento grandes
