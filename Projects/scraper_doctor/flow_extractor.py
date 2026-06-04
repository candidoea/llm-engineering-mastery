"""
flow_extractor.py — Extrai o fluxo de navegação do scraper via AST.

Responsabilidade: dado um script Selenium, produz uma sequência ordenada
de ações (get, send_keys, click, wait, select) que o crawler genérico
pode reproduzir para capturar o HTML de cada etapa.

Não conhece nenhum site específico — lê o script e reproduz o que encontra.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FlowAction:
    """Uma ação de navegação extraída do script original."""
    kind: str           # get, send_keys, click, wait, select, wait_for
    line: int           # linha no script original
    selector: tuple[str, str] | None = None   # (strategy, value) se aplicável
    value: str | None = None                  # valor para send_keys/select/get
    is_credential: bool = False               # se usa USER_EMAIL/USER_PASSWORD


@dataclass
class NavigationStage:
    """
    Etapa de navegação derivada do script original.

    Uma nova etapa começa após cada driver.get() ou bloco
    de comentário de seção (# ===).
    """
    name: str
    url: str | None
    actions: list[FlowAction] = field(default_factory=list)

    @property
    def has_login(self) -> bool:
        """Verifica se esta etapa contém ações de login."""
        return any(a.is_credential for a in self.actions)


class FlowVisitor(ast.NodeVisitor):
    """
    Percorre a AST do scraper e extrai o fluxo de navegação
    como sequência de ações ordenadas por linha.
    """

    def __init__(self, source_lines: list[str]):
        self.actions: list[FlowAction] = []
        self.source_lines = source_lines
        self._credential_vars: set[str] = set()  # variáveis que guardam credenciais

    def visit_Assign(self, node: ast.Assign):
        """Detecta variáveis de credenciais (USER_EMAIL, USER_PASSWORD, etc.)."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id.upper()
                if any(k in name for k in ("EMAIL", "PASSWORD", "USER", "LOGIN", "SENHA", "USUARIO")):
                    self._credential_vars.add(target.id)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Attribute):
            self.generic_visit(node)
            return

        attr = node.func.attr

        # driver.get("url")
        if attr == "get" and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant):
                self.actions.append(FlowAction(
                    kind="get",
                    line=node.lineno,
                    value=str(arg.value),
                ))

        # .send_keys(valor)
        elif attr == "send_keys" and node.args:
            selector = self._extract_selector_from_chain(node)
            value_node = node.args[0]
            is_cred = self._is_credential(value_node)
            value = self._extract_value(value_node)

            self.actions.append(FlowAction(
                kind="send_keys",
                line=node.lineno,
                selector=selector,
                value=value,
                is_credential=is_cred,
            ))

        # .click()
        elif attr == "click":
            selector = self._extract_selector_from_chain(node)
            self.actions.append(FlowAction(
                kind="click",
                line=node.lineno,
                selector=selector,
            ))

        # time.sleep(n)
        elif attr == "sleep" and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant):
                self.actions.append(FlowAction(
                    kind="wait",
                    line=node.lineno,
                    value=str(arg.value),
                ))

        # Select(elem).select_by_value("x")
        elif attr == "select_by_value" and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant):
                selector = self._extract_selector_from_chain(node)
                self.actions.append(FlowAction(
                    kind="select",
                    line=node.lineno,
                    selector=selector,
                    value=str(arg.value),
                ))

        # execute_script("arguments[0].click()", elem)
        elif attr == "execute_script":
            selector = self._extract_selector_from_args(node)
            if selector:
                self.actions.append(FlowAction(
                    kind="click_js",
                    line=node.lineno,
                    selector=selector,
                ))

        # wait.until(EC.presence_of_element_located((By.X, "v")))
        # wait.until(EC.element_to_be_clickable((By.X, "v")))
        elif attr == "until" and node.args:
            selector = self._extract_selector_from_ec(node.args[0])
            if selector:
                self.actions.append(FlowAction(
                    kind="wait_for",
                    line=node.lineno,
                    selector=selector,
                ))

        self.generic_visit(node)

    def _extract_selector_from_chain(self, node: ast.Call) -> tuple[str, str] | None:
        """
        Extrai seletor da cadeia de chamadas.
        Ex: driver.find_element(By.ID, "x").send_keys(...)
        """
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Call):
            return self._extract_selector_from_call(func.value)
        return None

    def _extract_selector_from_call(self, node: ast.Call) -> tuple[str, str] | None:
        """Extrai seletor de find_element(By.X, 'v') ou wait.until(EC.*(...)"""
        if not isinstance(node.func, ast.Attribute):
            return None

        if node.func.attr in ("find_element", "find_elements") and len(node.args) >= 2:
            return self._extract_by_args(node.args[0], node.args[1])

        return self._extract_selector_from_ec(node)

    def _extract_selector_from_ec(self, node: ast.expr) -> tuple[str, str] | None:
        """Extrai seletor de EC.presence_of_element_located((By.X, 'v'))"""
        if not isinstance(node, ast.Call):
            return None
        if not node.args:
            return None
        arg = node.args[0]
        if isinstance(arg, ast.Tuple) and len(arg.elts) >= 2:
            return self._extract_by_args(arg.elts[0], arg.elts[1])
        return None

    def _extract_selector_from_args(self, node: ast.Call) -> tuple[str, str] | None:
        """Extrai seletor de execute_script('...', element_var)"""
        for arg in node.args:
            if isinstance(arg, ast.Call):
                result = self._extract_selector_from_call(arg)
                if result:
                    return result
        return None

    def _extract_by_args(self, strategy_node, value_node) -> tuple[str, str] | None:
        if not (
            isinstance(strategy_node, ast.Attribute)
            and isinstance(strategy_node.value, ast.Name)
            and strategy_node.value.id == "By"
        ):
            return None

        strategy = strategy_node.attr

        if isinstance(value_node, ast.Constant):
            return (strategy, str(value_node.value))
        elif isinstance(value_node, ast.Name):
            return (strategy, f"<var:{value_node.id}>")
        return None

    def _is_credential(self, node: ast.expr) -> bool:
        """Verifica se um nó AST referencia uma variável de credencial."""
        if isinstance(node, ast.Name):
            return node.id in self._credential_vars
        return False

    def _extract_value(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Name):
            return f"<var:{node.id}>"
        return None


def extract_flow(path: str | Path) -> list[NavigationStage]:
    """
    Lê um script Selenium e extrai o fluxo de navegação como
    lista de etapas, cada uma com suas ações ordenadas.

    Etapas são delimitadas por:
    1. driver.get() — nova URL = nova etapa
    2. Blocos de comentário # === — divisores explícitos

    Returns:
        Lista de NavigationStage em ordem de execução
    """
    source = Path(path).read_text(encoding="utf-8", errors="ignore")
    lines = source.splitlines()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise ValueError(f"Erro de sintaxe: {e}") from e

    visitor = FlowVisitor(lines)
    visitor.visit(tree)

    # Ordena todas as ações por linha
    all_actions = sorted(visitor.actions, key=lambda a: a.line)

    if not all_actions:
        return []

    # Agrupa em etapas: nova etapa começa em cada "get" ou comentário de seção
    stages: list[NavigationStage] = []
    current_stage = NavigationStage(name="etapa_01", url=None, actions=[])
    stage_num = 1

    # Detecta linhas de comentário divisoras
    section_breaks = set()
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("# ===") or stripped.startswith("# ---"):
            section_breaks.add(i)

    for action in all_actions:
        # Nova URL = nova etapa (exceto a primeira)
        if action.kind == "get":
            if current_stage.actions or current_stage.url:
                stages.append(current_stage)
                stage_num += 1
            current_stage = NavigationStage(
                name=f"etapa_{stage_num:02d}",
                url=action.value,
                actions=[action],
            )
            continue

        # Comentário divisor próximo = nova etapa
        nearby_break = any(
            abs(action.line - b) <= 3
            for b in section_breaks
        )
        if nearby_break and current_stage.actions:
            stages.append(current_stage)
            stage_num += 1
            current_stage = NavigationStage(
                name=f"etapa_{stage_num:02d}",
                url=None,
                actions=[],
            )

        current_stage.actions.append(action)

    if current_stage.actions or current_stage.url:
        stages.append(current_stage)

    return stages


def summarize_flow(stages: list[NavigationStage]) -> str:
    """Resumo legível do fluxo extraído."""
    lines = [f"Fluxo extraído: {len(stages)} etapa(s)"]
    for stage in stages:
        url_str = f" → {stage.url}" if stage.url else ""
        login_str = " [LOGIN]" if stage.has_login else ""
        lines.append(f"  {stage.name}{url_str}{login_str}")
        for action in stage.actions[:5]:  # máx 5 ações por etapa no resumo
            sel_str = f" ({action.selector[0]}: {action.selector[1][:40]})" if action.selector else ""
            val_str = f" = {action.value[:30]}" if action.value and action.kind != "get" else ""
            cred_str = " [CRED]" if action.is_credential else ""
            lines.append(f"    L{action.line:3d} {action.kind}{sel_str}{val_str}{cred_str}")
        if len(stage.actions) > 5:
            lines.append(f"    ... +{len(stage.actions) - 5} ação(ões)")
    return "\n".join(lines)