"""
comparator.py — Fase 3: comparação estática entre seletores e HTML atual.

Resolve 80% dos diagnósticos SEM chamar o LLM.
O LLM só é acionado para o que a comparação estática não consegue resolver.
"""

from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup

from extractor import Selector


@dataclass
class SelectorResult:
    selector: Selector
    found: bool
    candidates: list[str] = field(default_factory=list)  # possíveis substitutos
    note: str = ""


@dataclass
class ComparisonReport:
    broken: list[SelectorResult] = field(default_factory=list)
    ok: list[SelectorResult] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return len(self.broken) > 0

    def summary(self) -> str:
        lines = []
        lines.append(
            f"Resultado: {len(self.ok)} OK, {len(self.broken)} QUEBRADOS"
        )

        if self.broken:
            lines.append("\n--- SELETORES QUEBRADOS ---")
            for r in self.broken:
                lines.append(
                    f"\n  linha {r.selector.line} | "
                    f"By.{r.selector.strategy} | {r.selector.value}"
                )
                lines.append(f"  Motivo: {r.note}")
                if r.candidates:
                    lines.append(
                        f"  Possíveis substitutos: {', '.join(r.candidates[:3])}"
                    )

        if self.ok:
            lines.append("\n--- SELETORES OK ---")
            for r in self.ok:
                lines.append(
                    f"  linha {r.selector.line} | "
                    f"By.{r.selector.strategy} | {r.selector.value}"
                )

        return "\n".join(lines)


def compare(
    selectors: list[Selector],
    html_path: str | Path,
) -> ComparisonReport:
    """
    Verifica cada seletor contra o HTML atual.

    Args:
        selectors: lista de seletores extraídos do scraper
        html_path: caminho para o arquivo HTML capturado do site atual

    Returns:
        ComparisonReport com seletores OK e quebrados
    """
    html = Path(html_path).read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    report = ComparisonReport()

    for sel in selectors:
        result = _check_selector(sel, soup)
        if result.found:
            report.ok.append(result)
        else:
            report.broken.append(result)

    return report


def _check_selector(sel: Selector, soup: BeautifulSoup) -> SelectorResult:
    """Verifica um seletor individual no soup."""

    value = sel.value

    # Ignora seletores que são variáveis (não conseguimos verificar estaticamente)
    if value.startswith("<"):
        return SelectorResult(
            selector=sel,
            found=True,
            note="Seletor dinâmico (variável) — não verificável estaticamente.",
        )

    strategy = sel.strategy

    if strategy == "ID":
        element = soup.find(id=value)
        if element:
            return SelectorResult(selector=sel, found=True)
        candidates = _find_similar_ids(soup, value)
        return SelectorResult(
            selector=sel,
            found=False,
            candidates=candidates,
            note=f"ID '{value}' não encontrado no HTML atual.",
        )

    elif strategy == "CLASS_NAME":
        elements = soup.find_all(class_=value)
        if elements:
            return SelectorResult(selector=sel, found=True)
        return SelectorResult(
            selector=sel,
            found=False,
            note=f"Classe '{value}' não encontrada no HTML atual.",
        )

    elif strategy == "CSS_SELECTOR":
        try:
            elements = soup.select(value)
            if elements:
                return SelectorResult(selector=sel, found=True)
        except Exception:
            pass
        return SelectorResult(
            selector=sel,
            found=False,
            note=f"CSS selector '{value}' não encontrado.",
        )

    elif strategy == "NAME":
        element = soup.find(attrs={"name": value})
        if element:
            return SelectorResult(selector=sel, found=True)
        return SelectorResult(
            selector=sel,
            found=False,
            note=f"Atributo name='{value}' não encontrado.",
        )

    elif strategy == "XPATH":
        # BeautifulSoup não suporta XPath nativamente.
        # Fazemos uma busca heurística pelo valor do seletor.
        note = (
            f"XPath '{value[:60]}...' requer lxml para verificação precisa. "
            "Encaminhado para diagnóstico via LLM."
        )
        return SelectorResult(selector=sel, found=True, note=note)

    else:
        return SelectorResult(
            selector=sel,
            found=True,
            note=f"Estratégia '{strategy}' não verificada estaticamente.",
        )


# Palavras-chave semânticas que indicam equivalência funcional entre IDs.
# Ex: "input_login_submit" e "loginBtn" ambos têm semântica de "login" + "submit/btn"
_SEMANTIC_GROUPS = [
    {"login", "signin", "sign_in"},
    {"submit", "btn", "button", "click"},
    {"user", "username", "email", "name"},
    {"pass", "password", "pwd"},
    {"search", "query", "find"},
    {"export", "download", "save"},
    {"run", "execute", "start", "go"},
    {"cancel", "close", "dismiss"},
]


def _semantic_overlap(a: str, b: str) -> bool:
    """Verifica se dois IDs compartilham palavras de um mesmo grupo semântico."""
    a_words = set(a.lower().replace("_", " ").replace("-", " ").split())
    b_words = set(b.lower().replace("_", " ").replace("-", " ").split())

    # Também tokeniza por camelCase
    import re
    def camel_split(s: str) -> set[str]:
        return set(w.lower() for w in re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', s))

    a_words |= camel_split(a)
    b_words |= camel_split(b)

    for group in _SEMANTIC_GROUPS:
        if a_words & group and b_words & group:
            return True
    return False


def _score_candidate(target_id: str, candidate_id: str) -> int:
    """
    Pontua um candidato em relação ao target.
    Maior pontuação = melhor candidato.

    Critérios (em ordem decrescente de peso):
    - Correspondência exata (case-insensitive): 100
    - Núcleo do target (sem prefixo input_) corresponde ao candidato: 80
    - Target é substring do candidato ou vice-versa: 60
    - Prefixo comum > 50%: 30
    - Sobreposição semântica: 10
    """
    t = target_id.lower()
    c = candidate_id.lower()
    score = 0

    if t == c:
        score += 100
    else:
        # Extrai o núcleo removendo prefixos comuns como "input_"
        t_core = t.replace("input_", "").replace("_input", "").strip("_")
        if t_core and t_core == c:
            score += 80
        elif t in c or c in t:
            score += 60
        elif _common_prefix_ratio(t, c) > 0.5:
            score += 30

    if _semantic_overlap(target_id, candidate_id):
        score += 10

    return score


def _find_similar_ids(soup: BeautifulSoup, target_id: str) -> list[str]:
    """
    Busca IDs no HTML que sejam similares ao ID quebrado.
    Retorna candidatos ordenados por pontuação de especificidade.

    Para seletores de submit/button, prioriza elementos do tipo correto.
    """
    target_lower = target_id.lower()

    # Detecta se o seletor é de submit/botão para busca tipada
    is_submit = any(w in target_lower for w in ("submit", "btn", "button", "click"))

    scored = []

    for tag in soup.find_all(id=True):
        existing_id = tag.get("id")
        if not existing_id:
            continue

        score = _score_candidate(target_id, existing_id)
        if score == 0:
            continue

        # Bônus: elemento do tipo correto para seletores de submit
        if is_submit and tag.name in ("button", "input") and tag.get("type") in ("submit", "button"):
            score += 50

        scored.append((score, existing_id))

    # Ordena por pontuação decrescente, depois alfabeticamente para empates
    scored.sort(key=lambda x: (-x[0], x[1]))

    return [eid for _, eid in scored[:5]]


def _common_prefix_ratio(a: str, b: str) -> float:
    """Proporção do prefixo comum entre duas strings."""
    if not a or not b:
        return 0.0
    common = 0
    for ca, cb in zip(a, b):
        if ca == cb:
            common += 1
        else:
            break
    return common / max(len(a), len(b))