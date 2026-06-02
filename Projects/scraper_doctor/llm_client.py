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


def generate_po_report(
    replacements: dict,
    stages_analyzed: list[str],
    model: str | None = None,
) -> str:
    """
    Gera um relatório de contexto em linguagem natural para o PO.

    Não busca substitutos — analisa o que as mudanças identificadas
    significam em termos de risco, padrão e sazonalidade.

    Args:
        replacements: dict {seletor_original: {substituto, estrategia, motivo}}
        stages_analyzed: etapas do fluxo que foram analisadas
        model: modelo a usar (None = OLLAMA_MODEL_FAST)

    Returns:
        Relatório em texto, em português, direcionado ao PO
    """
    if not replacements:
        return (
            "Nenhuma alteração detectada nas etapas analisadas. "
            "O scraper deve estar funcionando corretamente."
        )

    changes_text = "\n".join([
        f"- '{original}' substituído por '{info.get('substituto', 'não determinado')}'"
        f" (estratégia: By.{info.get('estrategia', '?')})"
        f" | origem: {info.get('origem', '?')}"
        for original, info in replacements.items()
    ])

    etapas_text = ", ".join(stages_analyzed) if stages_analyzed else "não informadas"

    system = (
        "Você é um analista de automação. "
        "Contexto: existe um script Python de web scraping que automatiza "
        "tarefas em um site. O site mudou seu HTML e o script quebrou. "
        "O Scraper Doctor identificou as mudanças e corrigiu o script automaticamente. "
        "Seu papel é explicar ao Product Owner o que aconteceu com o script "
        "e quais riscos existem para a automação — não para o site. "
        "Responda SEMPRE em português do Brasil. "
        "Use APENAS as informações fornecidas — nunca invente dados. "
        "Seja conciso: máximo 3 linhas por seção."
    )

    prompt = f"""O script de automação quebrou porque o site alterou seus elementos HTML.
O Scraper Doctor detectou e corrigiu automaticamente as seguintes mudanças:

ETAPAS DO FLUXO ANALISADAS: {etapas_text}

CORREÇÕES APLICADAS NO SCRIPT (elemento antigo → elemento novo no site):
{changes_text}

Responda EXATAMENTE neste formato, sem adicionar nada além:

## O que aconteceu com o script
[1-2 frases: o site mudou X e o script parou de funcionar nesse ponto]

## As mudanças parecem
[1 frase: planejadas/permanentes ou acidentais/temporárias — baseado no padrão observado]

## Risco para a automação
[1 frase: se o site mudar novamente nessas etapas, o script pode quebrar de novo — o que monitorar]

Não use saudações, assinaturas, listas com traço ou informações não fornecidas."""

    return ask(prompt, system=system, model=model, stream=True)