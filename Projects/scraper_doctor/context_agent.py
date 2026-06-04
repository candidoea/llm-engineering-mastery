"""
context_agent.py — Agente de contexto: lê o script original e extrai
intenções de navegação em linguagem estruturada.

Resolve a circularidade do crawler genérico:
  ANTES: crawler reproduz seletores antigos → falha porque estão quebrados
  AGORA: LLM lê o script → entende a INTENÇÃO de cada etapa
         → comparador busca elementos que cumpram essa intenção no HTML atual
         → independente dos seletores originais

Arquitetura multi-agent:
  Agente 1 (este módulo): contexto/raciocínio — lê script, produz intenções
  Agente 2 (comparator + diagnose_with_llm): execução — mapeia intenção→seletor
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from config import OLLAMA_MODEL_FAST


@dataclass
class StageIntent:
    """Intenção de uma etapa de navegação extraída do script."""
    name: str                    # nome descritivo (ex: "login", "navegacao_relatorios")
    objective: str               # o que esta etapa faz em linguagem natural
    stage_type: str              # login, navigation, form_submit, download, wait
    url: str | None              # URL se houver driver.get()
    fields_needed: list[str]     # tipos de campos necessários (ex: ["usuario", "senha", "submit"])
    success_indicator: str       # como saber se a etapa funcionou
    original_selectors: list[str] = field(default_factory=list)  # seletores originais (referência)


@dataclass
class ScriptContext:
    """Contexto completo extraído do script original."""
    script_purpose: str          # o que o script faz no geral
    stages: list[StageIntent]    # etapas em ordem de execução
    requires_auth: bool          # precisa de login?
    target_site: str | None      # site alvo identificado


def extract_context(
    scraper_path: str | Path,
    model: str | None = None,
) -> ScriptContext:
    """
    Lê o script original e usa o LLM para extrair o contexto de navegação.

    O LLM não tenta encontrar seletores — apenas entende o que o script faz.
    Retorna intenções estruturadas que guiam o diagnóstico posterior.

    Args:
        scraper_path: caminho para o script original
        model: modelo Ollama a usar (padrão: OLLAMA_MODEL_FAST)

    Returns:
        ScriptContext com intenções por etapa
    """
    from llm_client import ask

    source = Path(scraper_path).read_text(encoding="utf-8", errors="ignore")

    # Remove credenciais reais antes de enviar ao LLM
    import re
    source_safe = re.sub(
        r'(USER_EMAIL|USER_PASSWORD|TARGET_USERNAME|TARGET_PASSWORD)\s*=\s*["\'][^"\']*["\']',
        r'\1 = "<REDACTED>"',
        source,
    )

    # Limita o tamanho do script enviado
    if len(source_safe) > 4000:
        source_safe = source_safe[:4000] + "\n... [truncado]"

    system = (
        "Você é um analista de automação web. "
        "Leia scripts Selenium e extraia as INTENÇÕES de navegação — "
        "o que cada etapa faz, não como ela faz. "
        "Responda APENAS com JSON válido, sem markdown, sem texto adicional. "
        "Responda em português do Brasil."
    )

    prompt = f"""Analise este script Python de web scraping com Selenium.

SCRIPT:
{source_safe}

Extraia as intenções de navegação e retorne EXATAMENTE neste formato JSON:
{{
  "script_purpose": "descrição em uma frase do que o script faz",
  "requires_auth": true,
  "target_site": "nome do site (ex: Five9, Salesforce, etc)",
  "stages": [
    {{
      "name": "login",
      "objective": "autenticar o usuário no sistema com email e senha",
      "stage_type": "login",
      "url": "https://...",
      "fields_needed": ["campo_usuario", "campo_senha", "botao_submit"],
      "success_indicator": "página muda após clicar em submit",
      "original_selectors": ["input_username", "input_password", "input_login_submit"]
    }},
    {{
      "name": "navegacao_relatorios",
      "objective": "clicar no menu Dashboard & Reports",
      "stage_type": "navigation",
      "url": null,
      "fields_needed": ["link_ou_botao_relatorios"],
      "success_indicator": "página de relatórios carregada",
      "original_selectors": ["//span[contains(text(), 'Dashboard & Reports')]"]
    }}
  ]
}}

Identifique TODAS as etapas do script. Tipos válidos: login, navigation, form_submit, select_option, download, wait.
Não invente campos — baseie-se apenas no código fornecido."""

    print("[CONTEXT] Analisando script com LLM...")
    raw = ask(prompt, system=system, model=model or OLLAMA_MODEL_FAST, stream=False)

    # Parse do JSON
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if "```" in clean:
            clean = clean[:clean.rfind("```")].rstrip()
        clean = clean.strip()

        data = json.loads(clean)

        stages = []
        for s in data.get("stages", []):
            stages.append(StageIntent(
                name=s.get("name", "etapa"),
                objective=s.get("objective", ""),
                stage_type=s.get("stage_type", "navigation"),
                url=s.get("url"),
                fields_needed=s.get("fields_needed", []),
                success_indicator=s.get("success_indicator", ""),
                original_selectors=s.get("original_selectors", []),
            ))

        ctx = ScriptContext(
            script_purpose=data.get("script_purpose", ""),
            stages=stages,
            requires_auth=data.get("requires_auth", False),
            target_site=data.get("target_site"),
        )

        print(f"[CONTEXT] Contexto extraído: {len(stages)} etapa(s) identificada(s)")
        return ctx

    except json.JSONDecodeError as e:
        print(f"[CONTEXT] Aviso: JSON inválido ({e}) — usando contexto mínimo")
        return _fallback_context(scraper_path)


def _fallback_context(scraper_path: str | Path) -> ScriptContext:
    """
    Contexto mínimo extraído sem LLM quando o JSON falha.
    Usa o flow_extractor para derivar etapas estruturais.
    """
    from flow_extractor import extract_flow

    stages_flow = extract_flow(scraper_path)
    stages = []

    for i, stage in enumerate(stages_flow):
        has_login = stage.has_login
        stage_type = "login" if has_login else "navigation"
        objective = "autenticar usuário" if has_login else f"navegar — etapa {i+1}"

        selectors = [
            f"{a.selector[0]}:{a.selector[1]}"
            for a in stage.actions
            if a.selector and not a.selector[1].startswith("<")
        ]

        stages.append(StageIntent(
            name=stage.name,
            objective=objective,
            stage_type=stage_type,
            url=stage.url,
            fields_needed=[],
            success_indicator="",
            original_selectors=selectors,
        ))

    return ScriptContext(
        script_purpose="script de web scraping (contexto extraído por fallback)",
        stages=stages,
        requires_auth=any(s.has_login for s in stages_flow),
        target_site=None,
    )


def summarize_context(ctx: ScriptContext) -> str:
    """Resumo legível do contexto extraído."""
    lines = [
        f"Script: {ctx.script_purpose}",
        f"Site: {ctx.target_site or 'não identificado'}",
        f"Autenticação: {'Sim' if ctx.requires_auth else 'Não'}",
        f"Etapas ({len(ctx.stages)}):",
    ]
    for s in ctx.stages:
        url_str = f" [{s.url}]" if s.url else ""
        lines.append(f"  {s.name} ({s.stage_type}){url_str}")
        lines.append(f"    → {s.objective}")
        if s.fields_needed:
            lines.append(f"    → Campos: {', '.join(s.fields_needed)}")
    return "\n".join(lines)