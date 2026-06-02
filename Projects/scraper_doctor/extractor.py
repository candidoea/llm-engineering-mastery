"""
extractor.py — Extração de seletores Selenium via AST do Python.

Por que AST em vez de regex:
- Regex captura apenas padrões fixos (By.ID com aspas duplas).
- AST analisa a árvore sintática real do código, capturando:
  - Aspas simples ou duplas
  - Variáveis como seletor
  - By.CSS_SELECTOR, By.CLASS_NAME, By.NAME, By.TAG_NAME
  - find_element(By.ID, "valor") — args posicionais separados
  - wait.until(EC.method((By.ID, "valor"))) — tupla aninhada
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Selector:
    strategy: str   # ID, XPATH, CSS_SELECTOR, CLASS_NAME, NAME, TAG_NAME
    value: str      # O valor do seletor
    line: int       # Linha no código original
    stage: str = "unknown"  # Etapa do fluxo a que pertence (TASK-02)


@dataclass
class InfraIssue:
    """Problema de infraestrutura detectado no scraper (não é seletor HTML)."""
    line: int
    kind: str    # hardcoded_path, network_drive, binary_location
    value: str   # o valor problemático
    suggestion: str  # o que fazer


@dataclass
class ScraperProfile:
    selectors: list[Selector] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    infra_issues: list[InfraIssue] = field(default_factory=list)


class SelectorVisitor(ast.NodeVisitor):
    """
    Percorre a AST do scraper e extrai todas as chamadas
    envolvendo By.* em qualquer posição.
    """

    def __init__(self):
        self.selectors: list[Selector] = []
        self.urls: list[str] = []
        self.actions: list[str] = []
        self._seen: set[tuple] = set()  # evita duplicatas (linha, value)

    def _add_selector(self, strategy: str, value: str, line: int) -> None:
        """Adiciona seletor evitando duplicatas."""
        key = (line, value)
        if key not in self._seen:
            self._seen.add(key)
            self.selectors.append(Selector(
                strategy=strategy,
                value=value,
                line=line,
            ))

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute):
            # driver.get("url")
            if node.func.attr == "get" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    self.urls.append(arg.value)

            # Ações de interação
            if node.func.attr in ("click", "send_keys", "clear", "submit"):
                self.actions.append(f"linha {node.lineno}: {node.func.attr}()")

            # find_element(By.STRATEGY, "valor") — dois args posicionais
            if node.func.attr in ("find_element", "find_elements") and len(node.args) >= 2:
                self._extract_from_positional(node.args[0], node.args[1], node.lineno)

        # Tuplas (By.STRATEGY, "valor") em qualquer posição de argumento
        for arg in node.args:
            self._extract_from_tuple(arg, node.lineno)

        self.generic_visit(node)

    def _extract_from_positional(self, strategy_node, value_node, lineno: int) -> None:
        """
        Extrai seletor de find_element(By.STRATEGY, "valor").
        Os dois argumentos chegam separados, não como tupla.
        """
        if not (
            isinstance(strategy_node, ast.Attribute)
            and isinstance(strategy_node.value, ast.Name)
            and strategy_node.value.id == "By"
        ):
            return

        strategy = strategy_node.attr

        if isinstance(value_node, ast.Constant):
            value = str(value_node.value)
        elif isinstance(value_node, ast.Name):
            value = f"<variável: {value_node.id}>"
        else:
            value = "<expressão complexa>"

        self._add_selector(strategy, value, lineno)

    def _extract_from_tuple(self, arg, lineno: int) -> None:
        """
        Extrai seletor de uma tupla (By.STRATEGY, "valor").
        Padrão usado em wait.until(EC.method((By.ID, "x"))).
        """
        if not isinstance(arg, ast.Tuple) or len(arg.elts) < 2:
            return

        strategy_node, value_node = arg.elts[0], arg.elts[1]

        if not (
            isinstance(strategy_node, ast.Attribute)
            and isinstance(strategy_node.value, ast.Name)
            and strategy_node.value.id == "By"
        ):
            return

        strategy = strategy_node.attr

        if isinstance(value_node, ast.Constant):
            value = str(value_node.value)
        elif isinstance(value_node, ast.Name):
            value = f"<variável: {value_node.id}>"
        else:
            value = "<expressão complexa>"

        self._add_selector(strategy, value, lineno)


def _detect_infra_issues(source: str) -> list:
    """
    Detecta problemas de infraestrutura no código fonte do scraper.

    Padrões detectados:
    - Caminhos hardcoded para ChromeDriver/Chrome em drives não-padrão
    - binary_location hardcoded
    - Diretórios de rede hardcoded
    """
    import re

    issues = []

    for i, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()

        # Drive diferente de C: (ex: F:\, D:\)
        if any(f"{d}:\\" in stripped or f"{d}:/" in stripped for d in "ABDEFGHIJKLMNOPQRSTUVWXYZ"):
            issues.append(InfraIssue(
                line=i,
                kind="hardcoded_path",
                value=stripped[:80],
                suggestion=(
                    "Remova o caminho hardcoded. Use Service() sem argumentos "
                    "para que o Selenium Manager gerencie o driver automaticamente."
                )
            ))

        # binary_location hardcoded
        elif "binary_location" in stripped and "=" in stripped:
            issues.append(InfraIssue(
                line=i,
                kind="binary_location",
                value=stripped[:80],
                suggestion=(
                    "Remova options.binary_location. O Chrome instalado "
                    "no sistema será detectado automaticamente."
                )
            ))

        # Diretório de rede UNC hardcoded
        elif stripped.startswith("DOWNLOAD_DIR") and "\\" in stripped:
            issues.append(InfraIssue(
                line=i,
                kind="network_path",
                value=stripped[:80],
                suggestion=(
                    "Mova DOWNLOAD_DIR para o arquivo .env como "
                    "variável de ambiente."
                )
            ))

    return issues


def extract_from_file(path: str | Path) -> ScraperProfile:
    """
    Lê um arquivo Python e extrai o perfil completo do scraper.

    Args:
        path: caminho para o arquivo .py do scraper

    Returns:
        ScraperProfile com seletores, URLs e ações encontrados
    """
    source = Path(path).read_text(encoding="utf-8", errors="ignore")

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise ValueError(f"Erro de sintaxe no scraper: {e}") from e

    visitor = SelectorVisitor()
    visitor.visit(tree)

    # Ordena por linha para facilitar leitura
    visitor.selectors.sort(key=lambda s: s.line)

    infra_issues = _detect_infra_issues(source)

    return ScraperProfile(
        selectors=visitor.selectors,
        urls=visitor.urls,
        actions=visitor.actions,
        infra_issues=infra_issues,
    )


def summarize(profile: ScraperProfile) -> str:
    """Gera um resumo legível do perfil extraído."""
    lines = []

    lines.append(f"URLs acessadas ({len(profile.urls)}):")
    for url in profile.urls:
        lines.append(f"  {url}")

    lines.append(f"\nSeletores encontrados ({len(profile.selectors)}):")
    for sel in profile.selectors:
        lines.append(
            f"  linha {sel.line:3d} | By.{sel.strategy:<15} | {sel.stage:<20} | {sel.value}"
        )

    lines.append(f"\nAções de interação ({len(profile.actions)}):")
    for action in profile.actions:
        lines.append(f"  {action}")

    if profile.infra_issues:
        lines.append(f"\n⚠️  Problemas de infraestrutura detectados ({len(profile.infra_issues)}):")
        for issue in profile.infra_issues:
            lines.append(f"  linha {issue.line:3d} | {issue.kind:<18} | {issue.value}")
            lines.append(f"           → {issue.suggestion}")

    return "\n".join(lines)