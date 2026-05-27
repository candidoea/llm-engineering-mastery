#!/usr/bin/env bash
# =============================================================================
# setup.sh — Configura o ambiente de desenvolvimento completo
# Uso: bash scripts/setup.sh
# =============================================================================

set -euo pipefail

echo "=== LLM Engineering Mastery — Setup ==="

# --- Verifica Python ---
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_MAJOR=3
REQUIRED_MINOR=11

MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt "$REQUIRED_MAJOR" ] || [ "$MINOR" -lt "$REQUIRED_MINOR" ]; then
    echo "ERRO: Python $REQUIRED_MAJOR.$REQUIRED_MINOR+ necessário. Encontrado: $PYTHON_VERSION"
    exit 1
fi
echo "Python $PYTHON_VERSION — OK"

# --- Cria venv se não existir ---
if [ ! -d ".venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "Ambiente virtual ativado."

# --- Instala dependências ---
echo "Instalando dependências..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "Dependências instaladas."

# --- Configura .env ---
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Arquivo .env criado. Preencha com suas API keys antes de usar."
else
    echo ".env já existe — não sobrescrito."
fi

# --- Instala pre-commit hooks (opcional) ---
if command -v pre-commit &>/dev/null; then
    pre-commit install
    echo "Pre-commit hooks instalados."
fi

echo ""
echo "=== Setup concluído ==="
echo ""
echo "Para ativar o ambiente:"
echo "  source .venv/bin/activate"
echo ""
echo "Para abrir os notebooks:"
echo "  jupyter lab"
