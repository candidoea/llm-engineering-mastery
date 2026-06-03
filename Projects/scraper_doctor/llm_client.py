"""
llm_client.py — Cliente Ollama com timeout, streaming e formato estruturado.

Decisões:
- Prompt com formato JSON obrigatório para evitar texto prolixo
- LLM só é chamado quando comparador não encontrou substituto automático
- Retry automático em caso de conexão derrubada (WinError 10054)
"""

import json
import time

from openai import OpenAI

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL_CODE,
    OLLAMA_MODEL_FAST,
    OLLAMA_TIMEOUT,
)

MAX_RETRIES = 2
RETRY_DELAY = 5  # segundos entre retentativas


def _get_client() -> OpenAI:
    return OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
        timeout=OLLAMA_TIMEOUT,
    )


def ask(
    prompt: str,
    system: str = "",
    model: str | None = None,
    stream: bool = True,
) -> str:
    """
    Envia um prompt ao Ollama com retry automático em caso de falha de conexão.

    Args:
        prompt: mensagem do usuário
        system: system prompt
        model: modelo a usar (None = OLLAMA_MODEL_FAST)
        stream: exibe tokens em tempo real

    Returns:
        Resposta completa como string
    """
    client = _get_client()
    model = model or OLLAMA_MODEL_FAST

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    print(f"[LLM] Modelo: {model} | Prompt: {len(prompt)} chars")

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            if stream:
                return _stream(client, model, messages)
            else:
                return _blocking(client, model, messages)
        except Exception as e:
            if attempt <= MAX_RETRIES:
                print(f"[LLM] Erro na tentativa {attempt}: {e}")
                print(f"[LLM] Retentando em {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"[LLM] Falhou após {MAX_RETRIES + 1} tentativas.")
                raise


def _stream(client: OpenAI, model: str, messages: list) -> str:
    """Streaming com exibição em tempo real."""
    response_text = ""
    print("[LLM] Gerando...\n")

    with client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    ) as stream:
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            print(delta, end="", flush=True)
            response_text += delta

    print("\n")
    return response_text


def _blocking(client: OpenAI, model: str, messages: list) -> str:
    """Sem streaming — aguarda resposta completa."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content


def diagnose_with_llm(
    broken_without_candidates: list[dict],
    html_snippet: str,
    model: str | None = None,
) -> dict:
    """
    Chama o LLM APENAS para seletores sem substituto automático.
    Retorna JSON estruturado com substituto sugerido por seletor.

    Args:
        broken_without_candidates: lista de seletores sem substituto encontrado
            ex: [{"line": 81, "strategy": "CLASS_NAME", "value": "yui-navset-top"}]
        html_snippet: trecho do HTML com elementos interativos
        model: modelo a usar

    Returns:
        dict mapeando valor do seletor para substituto sugerido
        ex: {"yui-navset-top": "nav-container"}
    """
    if not broken_without_candidates:
        return {}

    selectors_text = "\n".join([
        f"- linha {s['line']}: By.{s['strategy']} '{s['value']}'"
        for s in broken_without_candidates
    ])

    system = (
        "Você é um especialista em Selenium. "
        "Responda SOMENTE em português do Brasil. "
        "Responda APENAS com JSON válido, sem texto adicional, sem markdown."
    )

    prompt = f"""Analise os seletores Selenium quebrados e o HTML atual.
Retorne um JSON com o substituto mais provável para cada seletor.

SELETORES QUEBRADOS (sem substituto automático encontrado):
{selectors_text}

HTML ATUAL (elementos interativos):
{html_snippet}

Retorne EXATAMENTE neste formato JSON, sem nenhum texto antes ou depois:
{{
  "diagnostico": [
    {{
      "seletor_original": "valor_original",
      "substituto": "valor_substituto_ou_null",
      "estrategia": "ID|CLASS_NAME|CSS_SELECTOR|XPATH",
      "motivo": "explicacao em uma linha"
    }}
  ]
}}

Se não conseguir determinar o substituto, use null."""

    raw = ask(prompt, system=system, model=model)

    # Tenta parsear JSON — se falhar, retorna vazio para não bloquear o fluxo
    try:
        # Remove possíveis blocos markdown que o modelo insira mesmo proibido
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = "\n".join(clean.split("\n")[:-1])

        data = json.loads(clean)
        result = {}
        for item in data.get("diagnostico", []):
            original = item.get("seletor_original", "")
            substituto = item.get("substituto")
            if original and substituto:
                result[original] = {
                    "substituto": substituto,
                    "estrategia": item.get("estrategia", ""),
                    "motivo": item.get("motivo", ""),
                }
        return result
    except json.JSONDecodeError:
        print("[LLM] Aviso: resposta não é JSON válido. Diagnóstico LLM ignorado.")
        return {}


def fix_with_llm(
    original_code: str,
    replacements: dict,
    model: str | None = None,
) -> str:
    """
    Gera scraper corrigido aplicando os substitutos encontrados.
    Usa substituição direta quando possível; LLM apenas para casos complexos.

    Args:
        original_code: código original do scraper
        replacements: dict {seletor_original: {substituto, estrategia, motivo}}
        model: modelo a usar

    Returns:
        Código Python corrigido
    """
    if not replacements:
        return original_code

    # Aplica substituições diretamente no código.
    # GUARDIÃO: só aplica se o seletor original realmente existe no código.
    # Impede que o LLM invente seletores que não estão no scraper original.
    fixed_code = original_code
    applied = []
    skipped = []

    for original, info in replacements.items():
        substituto = info.get("substituto")
        if not substituto or substituto == "null":
            continue

        exists_in_code = (
            f'"{original}"' in fixed_code
            or f"'{original}'" in fixed_code
        )

        if not exists_in_code:
            skipped.append(f"  '{original}' → IGNORADO (não existe no código original)")
            continue

        fixed_code = fixed_code.replace(
            f'"{original}"', f'"{substituto}"'
        ).replace(
            f"'{original}'", f"'{substituto}'"
        )
        applied.append(f"  {original} → {substituto}")

    if skipped:
        print("[CORREÇÃO] Ignorados (seletor não existe no código original):")
        for s in skipped:
            print(s)

    if applied:
        print("[CORREÇÃO] Aplicados:")
        for a in applied:
            print(a)

    # Substitui credenciais hardcoded por os.environ.get com fallback
    # Garante que o scraper_fixed.py usa sempre as credenciais do .env
    if "USER_EMAIL" in fixed_code or "USER_PASSWORD" in fixed_code:
        import re

        # Detecta e substitui USER_EMAIL = "valor_hardcoded"
        fixed_code = re.sub(
            r'(USER_EMAIL\s*=\s*)["\']([^"\']*)["\']',
            r'\1os.environ.get("TARGET_USERNAME", "\2")',
            fixed_code,
        )
        # Detecta e substitui USER_PASSWORD = "valor_hardcoded"
        fixed_code = re.sub(
            r'(USER_PASSWORD\s*=\s*)["\']([^"\']*)["\']',
            r'\1os.environ.get("TARGET_PASSWORD", "\2")',
            fixed_code,
        )
        # Garante que os e dotenv estão importados
        if "import os" not in fixed_code:
            fixed_code = "import os\n" + fixed_code
        if "load_dotenv" not in fixed_code:
            fixed_code = fixed_code.replace(
                "import os\n",
                "import os\nfrom dotenv import load_dotenv\nload_dotenv()\n",
                1,
            )
        print("[CORREÇÃO] Credenciais atualizadas para usar os.environ.get (com fallback)")

    # Se houver seletores que precisam de raciocínio mais complexo (XPath, CSS),
    # aciona o LLM apenas para esses
    complex_cases = {
        k: v for k, v in replacements.items()
        if v.get("estrategia") in ("XPATH", "CSS_SELECTOR")
        and v.get("substituto") is None
    }

    if complex_cases:
        print(f"[LLM] {len(complex_cases)} caso(s) complexo(s) — acionando LLM...")

        system = (
            "Você é um especialista em Selenium. "
            "Gere apenas código Python. "
            "Responda SEMPRE em português do Brasil."
        )

        cases_text = "\n".join([
            f"- By.{v['estrategia']} '{k}': {v.get('motivo', '')}"
            for k, v in complex_cases.items()
        ])

        prompt = f"""Corrija apenas estes seletores complexos no código Python abaixo:

{cases_text}

```python
{fixed_code[:6000]}
```

Retorne apenas o código Python corrigido, sem explicações."""

        fixed_code = ask(prompt, system=system, model=model or OLLAMA_MODEL_CODE)

    return fixed_code


def _ask_selectors_section(
    replacements: dict,
    stages_analyzed: list[str],
    model: str | None = None,
) -> str:
    """Prompt focado apenas nos seletores — contexto mínimo para o phi3."""
    etapas = ", ".join(stages_analyzed) if stages_analyzed else "não informadas"
    changes = "\n".join([
        f"- {orig} → {info.get('substituto', '?')}"
        for orig, info in replacements.items()
    ])

    system = (
        "Você é um analista de automação. "
        "Responda SEMPRE em português do Brasil. "
        "Use APENAS as informações fornecidas. "
        "Seja direto. Máximo 2 frases por seção."
    )

    prompt = f"""Um script de web scraping quebrou porque o site alterou seus elementos HTML.
O Scraper Doctor corrigiu automaticamente os seguintes seletores:

ETAPAS ANALISADAS: {etapas}
CORREÇÕES: {changes}

Responda EXATAMENTE assim, sem nada além:

## O que aconteceu
[1-2 frases: quais elementos mudaram e o que foi corrigido]

## As mudanças parecem
[1 frase: planejadas ou acidentais]

## Risco
[1 frase: o que monitorar para evitar nova quebra]"""

    return ask(prompt, system=system, model=model, stream=True)


def _build_infra_section(infra_issues: list) -> str:
    """
    Gera a seção de infraestrutura sem LLM — texto determinístico.
    Evita enviar infra_issues ao phi3, que degrada com contexto longo.
    """
    if not infra_issues:
        return ""

    KIND_LABELS = {
        "hardcoded_path": "Caminho hardcoded de ChromeDriver",
        "binary_location": "Binary location hardcoded do Chrome",
        "network_path": "Diretório de rede hardcoded",
    }

    lines = ["\n## Ação manual necessária"]
    lines.append(
        "Antes de executar o script corrigido, o time técnico deve ajustar:"
    )
    for issue in infra_issues:
        label = KIND_LABELS.get(issue.kind, issue.kind)
        lines.append(f"- **Linha {issue.line} — {label}:** {issue.suggestion}")

    return "\n".join(lines)


def generate_po_report(
    replacements: dict,
    stages_analyzed: list[str],
    infra_issues: list | None = None,
    model: str | None = None,
) -> str:
    """
    Gera relatório de contexto para o PO em duas partes independentes:
    1. Seção de seletores — gerada pelo LLM com prompt focado
    2. Seção de infraestrutura — gerada deterministicamente (sem LLM)

    Separar evita que o contexto de infra degrade a qualidade do LLM.
    """
    infra_issues = infra_issues or []

    if not replacements and not infra_issues:
        return (
            "Nenhuma alteração detectada nas etapas analisadas. "
            "O scraper deve estar funcionando corretamente."
        )

    parts = []

    # Parte 1: seletores via LLM (prompt pequeno e focado)
    if replacements:
        selectors_section = _ask_selectors_section(
            replacements=replacements,
            stages_analyzed=stages_analyzed,
            model=model,
        )
        parts.append(selectors_section)
    else:
        parts.append(
            "## O que aconteceu\n"
            "Nenhum seletor HTML foi alterado nas etapas analisadas.\n\n"
            "## As mudanças parecem\nNão aplicável.\n\n"
            "## Risco\nNenhum risco imediato identificado nos seletores."
        )

    # Parte 2: infraestrutura determinística (sem LLM)
    infra_section = _build_infra_section(infra_issues)
    if infra_section:
        parts.append(infra_section)

    return "\n\n".join(parts)