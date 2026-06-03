"""
doctor.py — Orquestrador do Scraper Doctor.

v0.3.0 — Diagnóstico por etapa (TASK-04):
- Cada seletor é comparado apenas contra o HTML da sua etapa
- Elimina falsos positivos (seletores de páginas internas marcados como
  quebrados no HTML de login)
- Para na primeira etapa com quebra real
"""

import sys
import time
from datetime import datetime
from pathlib import Path

from config import (
    HTML_STAGE_ORDER,
    MAX_PROMPT_CHARS,
    OLLAMA_MODEL_CODE,
    OLLAMA_MODEL_FAST,
    OUTPUT_DIR,
    REPORTS_DIR,
    SELECTOR_STAGE_MAP,
    build_stage_map,
)
from comparator import compare
from extractor import Selector, extract_from_file, summarize
from llm_client import diagnose_with_llm, fix_with_llm, generate_po_report
from metrics import RunMetrics


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _load_html(html_path: str | None, url: str | None) -> Path:
    if html_path and Path(html_path).exists():
        print(f"[HTML] Usando arquivo local: {html_path}")
        return Path(html_path)

    if url:
        try:
            import requests
            print(f"[HTML] Baixando HTML de: {url}")
            resp = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            })
            resp.raise_for_status()
            out_path = Path("html") / f"captured_{_timestamp()}.html"
            out_path.write_text(resp.text, encoding="utf-8")
            return out_path
        except Exception as e:
            print(f"[HTML] Falha: {e}")
            sys.exit(1)

    print("[ERRO] Forneça --html, --url ou --crawl.")
    sys.exit(1)


def _extract_relevant_html(html_path: Path) -> str:
    """Extrai snippet HTML com elementos interativos para o prompt do LLM."""
    from bs4 import BeautifulSoup

    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    tags = []
    for tag in soup.find_all(["input", "button", "a", "select", "form", "nav", "ul", "li"]):
        attrs = {k: v for k, v in tag.attrs.items()
                 if k in ("id", "name", "class", "type", "href", "action")}
        if attrs:
            tags.append(str(tag)[:200])

    snippet = "\n".join(tags)
    if len(snippet) > MAX_PROMPT_CHARS:
        snippet = snippet[:MAX_PROMPT_CHARS] + "\n... [truncado]"
    return snippet


def _apply_stage_map(selectors: list[Selector]) -> list[Selector]:
    """
    Anota cada seletor com sua etapa.

    Prioridade:
    1. SELECTOR_STAGE_MAP manual (config.py) — mais preciso
    2. build_stage_map automático — para seletores não mapeados
    3. 'unknown' — se nenhum mapa cobrir

    Quando mais de 30% dos seletores ficam como 'unknown',
    gera o mapa automático e avisa o usuário.
    """
    for sel in selectors:
        sel.stage = SELECTOR_STAGE_MAP.get(sel.line, "unknown")

    unknown_count = sum(1 for s in selectors if s.stage == "unknown")
    unknown_pct = unknown_count / len(selectors) if selectors else 0

    if unknown_pct > 0.30:
        print(
            f"  [AVISO] {unknown_count}/{len(selectors)} seletores sem stage mapeado "
            f"({unknown_pct:.0%}). Gerando mapeamento automático..."
        )
        auto_map = build_stage_map(
            [s for s in selectors if s.stage == "unknown"],
            HTML_STAGE_ORDER,
        )
        for sel in selectors:
            if sel.stage == "unknown" and sel.line in auto_map:
                sel.stage = auto_map[sel.line]
                sel.stage = f"{sel.stage}~auto"  # marca como automático
        print(
            "  [AVISO] Mapeamento automático aplicado. Para maior precisão, "
            "defina SELECTOR_STAGE_MAP em config.py após esta execução."
        )

    return selectors


def _diagnose_stage(
    stage_name: str,
    selectors: list[Selector],
    html_path: Path,
    fix: bool,
    ts: str,
    metrics: RunMetrics,
    scraper_path: str,
    include_unknown: bool = False,
) -> dict:
    """
    Executa diagnóstico para uma etapa específica.
    Compara apenas os seletores dessa etapa contra o HTML correspondente.

    Args:
        include_unknown: se True, inclui seletores sem stage mapeado.
                         Usado na última etapa para não perder seletores órfãos.

    Retorna dict de substitutos encontrados.
    """
    if include_unknown:
        stage_selectors = [
            s for s in selectors
            if s.stage == stage_name or s.stage == "unknown"
            or s.stage == f"{stage_name}~auto"
        ]
        unknown = [s for s in selectors if s.stage == "unknown"]
        if unknown:
            print(f"  [+] {len(unknown)} seletor(es) sem stage mapeado incluídos nesta etapa")
    else:
        stage_selectors = [
            s for s in selectors
            if s.stage == stage_name or s.stage == f"{stage_name}~auto"
        ]

    if not stage_selectors:
        return {}

    print(f"\n[FASE 3] Etapa '{stage_name}' — {len(stage_selectors)} seletor(es)")

    report = compare(stage_selectors, html_path)

    metrics.selectors_ok += len(report.ok)
    metrics.selectors_broken += len(report.broken)

    if report.ok:
        print(f"  OK:       {len(report.ok)} seletor(es)")

    if not report.has_issues:
        return {}

    print(f"  QUEBRADOS: {len(report.broken)} seletor(es)")
    for r in report.broken:
        subst = f" → substitutos: {', '.join(r.candidates)}" if r.candidates else ""
        print(f"    linha {r.selector.line}: '{r.selector.value}'{subst}")

    # Salva relatório da etapa
    report_path = REPORTS_DIR / f"static_report_{ts}_{stage_name}.txt"
    report_path.write_text(report.summary(), encoding="utf-8")

    # Separa: com substituto automático vs. sem
    with_candidates = [r for r in report.broken if r.candidates]
    without_candidates = [r for r in report.broken if not r.candidates]

    all_replacements = {}

    # Substitutos automáticos — sem LLM
    for r in with_candidates:
        best = r.candidates[0]
        all_replacements[r.selector.value] = {
            "substituto": best,
            "estrategia": r.selector.strategy,
            "motivo": f"Substituto encontrado por similaridade",
            "linha": r.selector.line,
            "origem": "estatico",
        }
        print(f"  AUTO: '{r.selector.value}' → '{best}'")

    # LLM apenas para seletores sem substituto
    if without_candidates:
        print(f"\n[FASE 4] {len(without_candidates)} seletor(es) sem substituto — consultando LLM...")

        broken_for_llm = [
            {"line": r.selector.line, "strategy": r.selector.strategy, "value": r.selector.value}
            for r in without_candidates
        ]

        html_snippet = _extract_relevant_html(html_path)

        t4 = time.perf_counter()
        llm_results = diagnose_with_llm(
            broken_without_candidates=broken_for_llm,
            html_snippet=html_snippet,
        )
        metrics.llm_time_s += time.perf_counter() - t4
        metrics.llm_calls += 1

        for k, v in llm_results.items():
            v["origem"] = "llm"
        all_replacements.update(llm_results)

        diagnosis_path = REPORTS_DIR / f"diagnosis_{ts}_{stage_name}.txt"
        diagnosis_path.write_text(
            "\n".join([
                f"linha {r.selector.line}: By.{r.selector.strategy} "
                f"'{r.selector.value}' → "
                f"{llm_results.get(r.selector.value, {}).get('substituto', 'não determinado')}"
                for r in without_candidates
            ]),
            encoding="utf-8",
        )
        print(f"[FASE 4] Diagnóstico salvo: diagnosis_{ts}_{stage_name}.txt")
    else:
        print(f"  Todos os substitutos encontrados estaticamente — LLM não necessário.")

    # Fase 5: gera scraper corrigido se solicitado
    if all_replacements and fix:
        print(f"\n[FASE 5] Aplicando correções da etapa '{stage_name}'...")
        original_code = Path(scraper_path).read_text(encoding="utf-8")

        t5 = time.perf_counter()
        fixed_code = fix_with_llm(
            original_code=original_code,
            replacements=all_replacements,
        )
        metrics.llm_time_s += time.perf_counter() - t5

        metrics.selectors_fixed += len([
            v for v in all_replacements.values()
            if v.get("substituto") and v.get("substituto") != "null"
        ])

        fixed_path = OUTPUT_DIR / f"scraper_fixed_{ts}.py"
        fixed_path.write_text(fixed_code, encoding="utf-8")
        print(f"[FASE 5] Scraper corrigido salvo: {fixed_path.name}")

    return all_replacements


def run(
    scraper_path: str,
    html_path: str | None = None,
    url: str | None = None,
    crawl: bool = False,
    visible: bool = False,
    fix: bool = False,
) -> None:
    start = time.perf_counter()
    ts = _timestamp()
    metrics = RunMetrics()
    metrics.model_diagnose = OLLAMA_MODEL_FAST
    metrics.model_fix = OLLAMA_MODEL_CODE

    print("\n" + "=" * 60)
    print("SCRAPER DOCTOR")
    print("=" * 60)

    # ------------------------------------------------------------------
    # FASE 1: Extração via AST + anotação de etapas
    # ------------------------------------------------------------------
    print("\n[FASE 1] Extraindo seletores via AST...")
    profile = extract_from_file(scraper_path)
    _apply_stage_map(profile.selectors)

    metrics.selectors_total = len(profile.selectors)

    print(f"  Seletores: {len(profile.selectors)}")
    print(f"  URLs:      {len(profile.urls)}")
    print(f"  Ações:     {len(profile.actions)}")
    if profile.infra_issues:
        print(f"  ⚠️  Infra:    {len(profile.infra_issues)} problema(s) detectado(s)")
    print()
    print(summarize(profile))

    if not profile.selectors:
        print("\n[AVISO] Nenhum seletor encontrado.")
        return

    # ------------------------------------------------------------------
    # FASE 2: Captura do HTML
    # ------------------------------------------------------------------
    print("\n[FASE 2] Carregando HTML atual...")

    if crawl:
        from crawler import crawl as do_crawl

        print("[FASE 2] Modo crawl: navegando no site com Selenium...")
        t_crawl = time.perf_counter()
        crawl_result = do_crawl(headless=not visible)
        metrics.crawl_time_s = time.perf_counter() - t_crawl

        if not crawl_result.pages:
            print("[ERRO] Nenhuma página capturada.")
            return

        if crawl_result.errors:
            print(f"\n[AVISO] {len(crawl_result.errors)} erro(s) durante o crawl:")
            for err in crawl_result.errors:
                # Mostra apenas primeira linha do erro (stacktrace é muito longo)
                print(f"  {err.splitlines()[0]}")

        print(f"\n[FASE 2] {len(crawl_result.pages)} página(s) capturada(s).\n")

        # ------------------------------------------------------------------
        # FASE 3: Diagnóstico por etapa na ordem correta
        # ------------------------------------------------------------------
        print("=" * 60)
        print("FASE 3 — Diagnóstico por etapa")
        print("=" * 60)

        found_broken = False
        all_replacements: dict = {}
        stages_analyzed: list[str] = []

        for stage_name in HTML_STAGE_ORDER:
            if stage_name not in crawl_result.pages:
                continue

            html_path_stage = crawl_result.pages[stage_name]
            metrics.stages_attempted += 1

            # Na última etapa disponível, inclui seletores sem stage mapeado
            is_last_stage = (stage_name == HTML_STAGE_ORDER[-1] or
                stage_name not in HTML_STAGE_ORDER[HTML_STAGE_ORDER.index(stage_name)+1:])
            available_stages = [s for s in HTML_STAGE_ORDER if s in crawl_result.pages]
            is_last_available = (stage_name == available_stages[-1])

            replacements = _diagnose_stage(
                stage_name=stage_name,
                selectors=profile.selectors,
                html_path=html_path_stage,
                fix=fix,
                ts=ts,
                metrics=metrics,
                scraper_path=scraper_path,
                include_unknown=is_last_available,
            )

            stages_analyzed.append(stage_name)

            if replacements:
                all_replacements.update(replacements)
                metrics.stages_failed += 1
                found_broken = True
                print(f"\n[STOP] Etapa '{stage_name}' tem seletores quebrados.")
                print("[STOP] Corrija e execute novamente para avançar.")
                break
            else:
                metrics.stages_completed += 1
                print(f"  ✓ Etapa '{stage_name}' — todos os seletores OK")

        if not found_broken:
            print("\n[OK] Todos os seletores estão corretos em todas as etapas.")

        # ------------------------------------------------------------------
        # RELATÓRIO DE CONTEXTO PARA O PO
        # Gerado sempre ao final — independente de ter encontrado quebras
        # ------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("RELATÓRIO DE CONTEXTO — Product Owner")
        print("=" * 60)

        t_po = time.perf_counter()
        po_report = generate_po_report(
            replacements=all_replacements,
            stages_analyzed=stages_analyzed,
            infra_issues=profile.infra_issues,
        )
        metrics.llm_time_s += time.perf_counter() - t_po
        if all_replacements:
            metrics.llm_calls += 1

        po_report_path = REPORTS_DIR / f"po_report_{ts}.txt"
        po_report_path.write_text(po_report, encoding="utf-8")
        print(f"\n[PO] Relatório salvo em: {po_report_path.name}")

    else:
        # Modo sem crawl: usa HTML único fornecido
        resolved_html = _load_html(html_path, url)
        _diagnose_stage(
            stage_name="manual",
            selectors=profile.selectors,
            html_path=resolved_html,
            fix=fix,
            ts=ts,
            metrics=metrics,
            scraper_path=scraper_path,
        )

    metrics.total_time_s = time.perf_counter() - start
    print(metrics.report())

    kpi_path = REPORTS_DIR / f"kpis_{ts}.json"
    metrics.save(str(kpi_path))
    print(f"[KPIs] Salvo em: {kpi_path.name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scraper Doctor")
    parser.add_argument("scraper", help="Caminho para o scraper .py")
    parser.add_argument("--html", default=None, help="HTML local")
    parser.add_argument("--url", default=None, help="URL para captura via requests")
    parser.add_argument("--crawl", action="store_true", help="Navega com Selenium")
    parser.add_argument("--visible", action="store_true", help="Chrome visível")
    parser.add_argument("--fix", action="store_true", help="Gera scraper corrigido")
    parser.add_argument(
        "--agent", action="store_true",
        help="Agent mode: valida o scraper_fixed.py e itera automaticamente"
    )
    parser.add_argument(
        "--iterations", type=int, default=3,
        help="Máximo de iterações do agent (default: 3)"
    )

    args = parser.parse_args()

    # Se --agent, executa o ciclo autônomo no scraper_fixed mais recente
    if args.agent:
        from agent import run_agent
        import glob

        fixed_files = sorted(
            glob.glob(str(OUTPUT_DIR / "scraper_fixed_*.py")),
            key=lambda f: Path(f).stat().st_mtime,
            reverse=True,
        )

        if not fixed_files:
            print("[AGENT] Nenhum scraper_fixed_*.py encontrado em output/")
            print("[AGENT] Execute primeiro: python doctor.py <scraper> --crawl --fix")
            sys.exit(1)

        latest_fixed = fixed_files[0]
        print(f"[AGENT] Usando scraper mais recente: {Path(latest_fixed).name}")

        run_agent(
            scraper_fixed_path=latest_fixed,
            max_iterations=args.iterations,
        )
        sys.exit(0)

    run(
        scraper_path=args.scraper,
        html_path=args.html,
        url=args.url,
        crawl=args.crawl,
        visible=args.visible,
        fix=args.fix,
    )