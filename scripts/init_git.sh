#!/usr/bin/env bash
# =============================================================================
# init_git.sh — Inicializa o repositório git com configuração correta
# Execute UMA VEZ após clonar ou criar o repositório
# =============================================================================

set -euo pipefail

echo "=== Inicializando repositório git ==="

# Inicializa se ainda não for um repo git
if [ ! -d ".git" ]; then
    git init
    echo "Repositório git inicializado."
fi

# Configura branches
git checkout -b main 2>/dev/null || git checkout main
git add .
git commit -m "feat: initial repository structure

Estrutura completa do repositório LLM Engineering Mastery:
- 00_foundations: matemática from scratch (álgebra linear, cálculo, probabilidade, teoria da informação)
- 01-08 weeks: módulos correspondentes ao curso AI Engineer Core Track
- 99_capstone: projeto integrador
- CI/CD: GitHub Actions para lint, testes e validação de notebooks
- Scripts: setup, validação e utilitários"

# Cria branch de desenvolvimento
git checkout -b develop
echo "Branch 'develop' criada."

echo ""
echo "=== Git inicializado ==="
echo ""
echo "Próximos passos:"
echo "  1. Crie o repositório no GitHub (não inicializado)"
echo "  2. git remote add origin https://github.com/SEU_USUARIO/llm-engineering-mastery.git"
echo "  3. git push -u origin main"
echo "  4. git push -u origin develop"
echo ""
echo "Configure o branch 'main' como protegido no GitHub:"
echo "  Settings > Branches > Add rule > Require PR reviews"
