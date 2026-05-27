"""
Wrapper unificado para chamadas a múltiplos provedores de LLM.

Design: interface única, backends intercambiáveis. Permite experimentação
comparativa sem modificar o código de chamada.

Padrão: Strategy pattern — cada provedor implementa o mesmo protocolo.
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMResponse:
    """Resposta normalizada de qualquer provedor."""

    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    raw_response: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class LLMRequest:
    """Requisição normalizada, independente de provedor."""

    prompt: str
    system_prompt: str = ""
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0


class LLMProvider(ABC):
    """Interface base para todos os provedores."""

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse:
        """Envia uma requisição e retorna resposta normalizada."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str: ...


class OpenAIProvider(LLMProvider):
    """Provedor OpenAI (GPT-4o, GPT-4-turbo, etc.)."""

    def __init__(self, api_key: Optional[str] = None):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError("pip install openai") from e

        self._client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"

    def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.default_model
        messages = []

        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        start = time.perf_counter()
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
        )
        latency = time.perf_counter() - start

        return LLMResponse(
            content=response.choices[0].message.content,
            model=model,
            provider="openai",
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            latency_seconds=latency,
            raw_response=response.model_dump(),
        )


class AnthropicProvider(LLMProvider):
    """Provedor Anthropic (Claude Sonnet, Claude Opus, etc.)."""

    def __init__(self, api_key: Optional[str] = None):
        try:
            import anthropic
        except ImportError as e:
            raise ImportError("pip install anthropic") from e

        key = api_key or os.environ["ANTHROPIC_API_KEY"]
        self._client = anthropic.Anthropic(api_key=key)

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-5"

    def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.default_model

        start = time.perf_counter()
        response = self._client.messages.create(
            model=model,
            max_tokens=request.max_tokens,
            system=request.system_prompt or "You are a helpful assistant.",
            messages=[{"role": "user", "content": request.prompt}],
            temperature=request.temperature,
            top_p=request.top_p,
        )
        latency = time.perf_counter() - start

        return LLMResponse(
            content=response.content[0].text,
            model=model,
            provider="anthropic",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_seconds=latency,
            raw_response=response.model_dump(),
        )


class LLMClient:
    """
    Cliente unificado que roteia para o provedor correto.

    Uso:
        client = LLMClient()
        response = client.complete("openai", LLMRequest(prompt="Explique atenção"))
    """

    _providers: dict[str, LLMProvider] = {}

    def register(self, name: str, provider: LLMProvider) -> "LLMClient":
        self._providers[name] = provider
        return self

    def complete(self, provider_name: str, request: LLMRequest) -> LLMResponse:
        if provider_name not in self._providers:
            raise KeyError(
                f"Provedor '{provider_name}' não registrado. "
                f"Disponíveis: {list(self._providers.keys())}"
            )
        return self._providers[provider_name].complete(request)

    def compare(self, request: LLMRequest) -> dict[str, LLMResponse]:
        """Envia o mesmo request para todos os provedores registrados."""
        return {
            name: provider.complete(request)
            for name, provider in self._providers.items()
        }
