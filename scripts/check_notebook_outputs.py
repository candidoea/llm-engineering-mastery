"""
Verifica que notebooks não têm outputs salvos.
Outputs devem ser limpos antes de commits para:
  1. Evitar vazar dados/API responses
  2. Manter diffs legíveis no git
  3. Garantir reprodutibilidade (quem rodar, verá os resultados frescos)

Para limpar: jupyter nbconvert --clear-output --inplace <notebook.ipynb>
"""

import json
import sys
from pathlib import Path


def has_outputs(path: Path) -> bool:
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)

    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            if cell.get("outputs"):
                return True
            if cell.get("execution_count") is not None:
                return True
    return False


def main() -> int:
    repo_root = Path(__file__).parent.parent
    notebooks = list(repo_root.rglob("*.ipynb"))
    notebooks = [nb for nb in notebooks if ".ipynb_checkpoints" not in str(nb)]

    dirty = []
    for nb_path in sorted(notebooks):
        if has_outputs(nb_path):
            dirty.append(nb_path.relative_to(repo_root))

    if dirty:
        print("Notebooks com outputs salvos (limpe antes de commitar):")
        for nb in dirty:
            print(f"  {nb}")
        print("\nPara limpar todos:")
        print("  find . -name '*.ipynb' | xargs jupyter nbconvert " "--clear-output --inplace")
        return 1

    print(f"Todos os {len(notebooks)} notebooks estão limpos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
