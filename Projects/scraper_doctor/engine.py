"""
engine.py — Motor de diagnóstico incremental por etapa.

Implementa o fluxo central do Modo 1:
  Para cada etapa do scraper original:
    1. Captura HTML da etapa atual
    2. Compara seletores da etapa com HTML
    3. Encontrou diferença? Testa script mínimo com candidato
    4. Passou? Avança. Não passou? Aciona LLM. Itera.
  Ao final: testa scraper completo com credenciais locais
  Funciona? Entrega scraper_fixed.py com ajustes mínimos no original.

A engine não conhece o Five9 nem nenhum site específico.
Ela lê o script original e navega baseada nele.
"""

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import os
from dotenv import load_dotenv
from pathlib import Path as _Path
load_dotenv(_Path(__file__).parent / ".env")

from config import HTML_DIR, OUTPUT_DIR, REPORTS_DIR
from comparator import compare, ComparisonReport
from extractor import ScraperProfile, Selector
from metrics import RunMetrics
from stage_runner import validate_stage

TARGET_URL = os.environ.get("TARGET_URL", "")


MAX_LLM_RETRIES = 2


@dataclass
class StageResult:
    """Resultado do diagnóstico de uma etapa."""
    stage_name: str
    selectors: list[Selector]
    broken: list
    fixes: dict[str, str] = field(default_factory=dict)  # original → substituto
    validated: bool = False
    skipped: bool = False


@dataclass
class EngineResult:
    """Resultado completo do ciclo de diagnóstico."""
    stages: list[StageResult] = field(default_factory=list)
    all_fixes: dict[str, str] = field(default_factory=dict)
    final_validated: bool = False
    scraper_fixed_path: Path | None = None
    total_time_s: float = 0.0

    @property
    def has_fixes(self) -> bool:
        return len(self.all_fixes) > 0


def _extract_stages_from_profile(
    profile: ScraperProfile,
    scraper_source: str = "",
) -> list[dict]:
    """
    Deriva etapas do fluxo a partir do ScraperProfile.

    Estratégia:
    1. Cada URL (driver.get) marca o início de uma etapa
    2. Blocos de comentário (# ===) são usados como divisores de etapa
    3. Seletores são agrupados por proximidade de linha entre divisores

    O TARGET_URL do .env substitui a URL do script quando disponível.

    Returns:
        Lista de dicts: {name, url, selectors}
    """
    if not profile.urls:
        return []

    sorted_selectors = sorted(profile.selectors, key=lambda s: s.line)

    # Detecta divisores de etapa por blocos de comentário no código
    stage_breaks = []  # linhas onde começa uma nova etapa
    if scraper_source:
        for i, line in enumerate(scraper_source.splitlines(), start=1):
            stripped = line.strip()
            # Comentários de seção são divisores de etapa
            if stripped.startswith("# ===") or stripped.startswith("# ---"):
                stage_breaks.append(i)

    # Se não encontrou divisores por comentário, divide por gap de linhas
    if not stage_breaks and len(sorted_selectors) > 3:
        # Detecta gaps grandes entre seletores como divisores naturais
        for j in range(1, len(sorted_selectors)):
            gap = sorted_selectors[j].line - sorted_selectors[j-1].line
            if gap > 15:  # gap > 15 linhas = nova etapa
                stage_breaks.append(sorted_selectors[j].line)

    # Agrupa seletores por etapa com base nos divisores
    stages_selectors = []
    if stage_breaks:
        current_group = []
        break_idx = 0
        for sel in sorted_selectors:
            if break_idx < len(stage_breaks) and sel.line >= stage_breaks[break_idx]:
                if current_group:
                    stages_selectors.append(current_group)
                current_group = [sel]
                break_idx += 1
            else:
                current_group.append(sel)
        if current_group:
            stages_selectors.append(current_group)
    else:
        stages_selectors = [sorted_selectors]

    # Monta etapas
    stages = []
    base_url = TARGET_URL if TARGET_URL else (profile.urls[0] if profile.urls else "")

    for i, group in enumerate(stages_selectors):
        # Primeira etapa usa a URL de login; demais usam a mesma (navegação interna)
        url = base_url if i == 0 else base_url
        stages.append({
            "name": f"etapa_{i+1:02d}",
            "url": url,
            "selectors": group,
            "is_first": i == 0,
        })

    return stages


def _extract_navigation_code_for_stage(
    scraper_source: str,
    stage_selectors: list[Selector],
) -> str:
    """
    Extrai o bloco de código do scraper original relevante para esta etapa.

    Usa as linhas dos seletores como âncoras para determinar o bloco.
    Inclui contexto suficiente para que o script mínimo funcione.
    """
    if not stage_selectors:
        return ""

    lines = scraper_source.splitlines()
    first_line = min(s.line for s in stage_selectors) - 1
    last_line = max(s.line for s in stage_selectors)

    # Expande contexto: 5 linhas antes e 10 depois para capturar wait/sleep
    start = max(0, first_line - 5)
    end = min(len(lines), last_line + 10)

    return "\n".join(lines[start:end])


def _get_next_stage_selector(
    stages: list[dict],
    current_idx: int,
) -> tuple[str, str] | None:
    """
    Retorna o primeiro seletor da próxima etapa para usar como assertion.
    """
    if current_idx + 1 >= len(stages):
        return None

    next_selectors = stages[current_idx + 1]["selectors"]
    if not next_selectors:
        return None

    # Pega o primeiro seletor estático (não variável) da próxima etapa
    for sel in next_selectors:
        if not sel.value.startswith("<"):
            return (sel.strategy, sel.value)

    return None


def run_engine(
    scraper_path: str | Path,
    scraper_source: str,
    profile: ScraperProfile,
    metrics: RunMetrics,
    headless: bool = True,
    llm_client=None,
) -> EngineResult:
    """
    Executa o motor de diagnóstico incremental.

    Args:
        scraper_path: caminho do scraper original
        scraper_source: código fonte do scraper
        profile: perfil extraído pelo extractor
        metrics: objeto de métricas para registrar KPIs
        headless: modo headless do Selenium
        llm_client: função ask() do llm_client para casos sem candidato

    Returns:
        EngineResult com todas as correções validadas
    """
    from html_fetcher import fetch_html
    from comparator import compare

    result = EngineResult()
    start = time.perf_counter()

    print("\n" + "=" * 60)
    print("ENGINE — DIAGNÓSTICO INCREMENTAL POR ETAPA")
    print("=" * 60)

    stages = _extract_stages_from_profile(profile, scraper_source)

    if not stages:
        print("[ENGINE] Nenhuma URL encontrada no scraper — sem etapas para analisar.")
        return result

    print(f"[ENGINE] {len(stages)} etapa(s) identificada(s)")

    # Loop incremental por etapa
    for i, stage in enumerate(stages):
        stage_name = stage["name"]
        url = stage["url"]
        stage_selectors = stage["selectors"]

        if not stage_selectors:
            print(f"\n[ENGINE] {stage_name}: sem seletores — pulando")
            continue

        print(f"\n{'─' * 60}")
        print(f"[ENGINE] {stage_name}: {url}")
        print(f"[ENGINE] Seletores: {len(stage_selectors)}")

        metrics.stages_attempted += 1

        # 2a. Captura HTML da etapa
        t_fetch = time.perf_counter()
        html_path = fetch_html(
            url=url,
            name=stage_name,
            use_selenium=True,
            headless=headless,
        )
        metrics.crawl_time_s += time.perf_counter() - t_fetch

        if not html_path:
            print(f"  [ENGINE] Não foi possível capturar HTML de {url}")
            stage_result = StageResult(
                stage_name=stage_name,
                selectors=stage_selectors,
                broken=[],
                skipped=True,
            )
            result.stages.append(stage_result)
            continue

        # 2b. Compara seletores com HTML
        report = compare(stage_selectors, html_path)
        metrics.selectors_total += len(stage_selectors)
        metrics.selectors_ok += len(report.ok)
        metrics.selectors_broken += len(report.broken)

        if not report.has_issues:
            print(f"  [ENGINE] ✓ Todos os seletores OK")
            stage_result = StageResult(
                stage_name=stage_name,
                selectors=stage_selectors,
                broken=[],
                validated=True,
            )
            result.stages.append(stage_result)
            metrics.stages_completed += 1
            continue

        print(f"  [ENGINE] {len(report.broken)} seletor(es) quebrado(s)")

        # 2c. Monta candidatos
        fixes = {}
        needs_llm = []

        for r in report.broken:
            if r.candidates:
                fixes[r.selector.value] = r.candidates[0]
                print(f"  AUTO: '{r.selector.value}' → '{r.candidates[0]}'")
            else:
                needs_llm.append(r.selector)
                print(f"  SEM CANDIDATO: '{r.selector.value}' → LLM necessário")

        # Aciona LLM para seletores sem candidato
        if needs_llm and llm_client:
            from llm_client import diagnose_with_llm
            import json

            broken_for_llm = [
                {"line": s.line, "strategy": s.strategy, "value": s.value}
                for s in needs_llm
            ]
            html_snippet = _extract_html_snippet(html_path)

            t_llm = time.perf_counter()
            llm_results = diagnose_with_llm(
                broken_without_candidates=broken_for_llm,
                html_snippet=html_snippet,
            )
            metrics.llm_time_s += time.perf_counter() - t_llm
            metrics.llm_calls += 1

            for original, info in llm_results.items():
                substituto = info.get("substituto")
                if substituto and substituto != "null":
                    fixes[original] = substituto
                    print(f"  LLM: '{original}' → '{substituto}'")

        # 2d. Valida via script mínimo
        nav_code = _extract_navigation_code_for_stage(scraper_source, stage_selectors)
        next_sel = _get_next_stage_selector(stages, i)

        # Etapas internas requerem login antes de navegar
        is_first = stage.get("is_first", i == 0)
        login_sels = result._login_selectors if hasattr(result, "_login_selectors") else None

        validated, validated_fixes = validate_stage(
            stage_name=stage_name,
            navigation_code=nav_code,
            selectors_with_fixes=fixes,
            next_stage_selector=next_sel,
            requires_login=not is_first,
            login_selectors=login_sels,
        )

        # Guarda seletores de login validados para uso nas etapas seguintes
        if is_first and validated:
            result._login_selectors = {
                "username_id": validated_fixes.get("input_username", fixes.get("input_username", "username")),
                "password_id": validated_fixes.get("input_password", fixes.get("input_password", "password")),
                "submit_id": validated_fixes.get("input_login_submit", fixes.get("input_login_submit", "loginBtn")),
            }

        stage_result = StageResult(
            stage_name=stage_name,
            selectors=stage_selectors,
            broken=report.broken,
            fixes=validated_fixes,
            validated=validated,
        )
        result.stages.append(stage_result)

        if validated:
            metrics.stages_completed += 1
            metrics.selectors_fixed += len(validated_fixes)
            result.all_fixes.update(validated_fixes)
            print(f"  [ENGINE] ✅ {stage_name} validado com {len(validated_fixes)} correção(ões)")
        else:
            metrics.stages_failed += 1
            print(f"  [ENGINE] ✗ {stage_name} não passou na validação")
            # Continua para as próximas etapas mesmo com falha
            # O relatório final indicará o que não foi possível validar

    result.total_time_s = time.perf_counter() - start
    return result


def _extract_html_snippet(html_path: Path, max_chars: int = 3000) -> str:
    """Extrai snippet de elementos interativos do HTML para o LLM."""
    from bs4 import BeautifulSoup

    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    tags = []
    for tag in soup.find_all(["input", "button", "a", "select", "form"]):
        attrs = {k: v for k, v in tag.attrs.items()
                 if k in ("id", "name", "class", "type", "href")}
        if attrs:
            tags.append(str(tag)[:200])

    snippet = "\n".join(tags)
    return snippet[:max_chars] if len(snippet) > max_chars else snippet


def apply_fixes_to_original(
    scraper_source: str,
    all_fixes: dict[str, str],
) -> str:
    """
    Aplica todas as correções validadas no código original.
    Guardião: só aplica onde o seletor original existe no código.
    """
    fixed = scraper_source
    applied = []
    skipped = []

    for original, substituto in all_fixes.items():
        if not substituto or substituto == "null":
            continue

        exists = f'"{original}"' in fixed or f"'{original}'" in fixed
        if not exists:
            skipped.append(original)
            continue

        fixed = fixed.replace(f'"{original}"', f'"{substituto}"')
        fixed = fixed.replace(f"'{original}'", f"'{substituto}'")
        applied.append(f"  '{original}' → '{substituto}'")

    if applied:
        print("\n[ENGINE] Correções aplicadas no original:")
        for a in applied:
            print(a)
    if skipped:
        print(f"\n[ENGINE] Ignorados (não encontrados no código): {skipped}")

    return fixed