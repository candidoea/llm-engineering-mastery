"""
Valida que todos os notebooks do repositório têm estrutura correta:
- São JSON válidos
- Têm metadados mínimos (título na primeira célula markdown)
- Kernel é python3
"""

import json
import sys
from pathlib import Path


def validate_notebook(path: Path) -> list[str]:
    errors = []

    try:
        with open(path, encoding="utf-8") as f:
            nb = json.load(f)
    except json.JSONDecodeError as e:
        return [f"JSON inválido: {e}"]

    # Kernel check
    kernel = nb.get("metadata", {}).get("kernelspec", {}).get("name", "")
    if kernel and kernel != "python3":
        errors.append(f"Kernel inesperado: {kernel} (esperado: python3)")

    # Primeira célula deve ser markdown com título
    cells = nb.get("cells", [])
    if not cells:
        errors.append("Notebook vazio (sem células)")
        return errors

    first = cells[0]
    if first.get("cell_type") != "markdown":
        errors.append("Primeira célula deve ser markdown com título do notebook")
    else:
        source = "".join(first.get("source", []))
        if not source.startswith("#"):
            errors.append("Primeira célula markdown deve começar com título (# ...)")

    return errors


def main() -> int:
    repo_root = Path(__file__).parent.parent
    notebooks = list(repo_root.rglob("*.ipynb"))
    notebooks = [nb for nb in notebooks if ".ipynb_checkpoints" not in str(nb)]

    if not notebooks:
        print("Nenhum notebook encontrado.")
        return 0

    total_errors = 0
    for nb_path in sorted(notebooks):
        errors = validate_notebook(nb_path)
        rel = nb_path.relative_to(repo_root)
        if errors:
            print(f"ERRO  {rel}")
            for err in errors:
                print(f"      - {err}")
            total_errors += len(errors)
        else:
            print(f"OK    {rel}")

    if total_errors:
        print(f"\n{total_errors} erro(s) encontrado(s).")
        return 1

    print(f"\n{len(notebooks)} notebook(s) validado(s) com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
