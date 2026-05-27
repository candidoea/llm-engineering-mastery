"""
Configuração global do pytest.
Fixtures compartilhadas entre todos os módulos.
"""

import os
import sys
from pathlib import Path

import pytest

# Garante que o root do projeto está no PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(scope="session")
def sample_vectors():
    """Vetores de exemplo para testes de álgebra linear."""
    return {
        "v1": [1.0, 0.0, 0.0],
        "v2": [0.0, 1.0, 0.0],
        "v3": [1.0, 1.0, 0.0],
        "zero": [0.0, 0.0, 0.0],
    }


@pytest.fixture(scope="session")
def sample_texts():
    """Textos de exemplo para testes de NLP."""
    return [
        "Transformers revolucionaram o processamento de linguagem natural.",
        "Attention is all you need.",
        "Large language models scale with data and compute.",
    ]
