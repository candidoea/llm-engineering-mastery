"""
Testes unitários para LLMClient.
Usa mocks para não depender de API keys em CI.
"""

from unittest.mock import patch

import pytest
from src.llm_client import LLMClient, LLMProvider, LLMRequest, LLMResponse


def make_mock_response(content: str = "resposta de teste") -> LLMResponse:
    return LLMResponse(
        content=content,
        model="mock-model",
        provider="mock",
        input_tokens=10,
        output_tokens=5,
        latency_seconds=0.1,
    )


class MockProvider(LLMProvider):
    def __init__(self, response_content: str = "ok"):
        self._response = response_content

    @property
    def default_model(self) -> str:
        return "mock-1"

    def complete(self, request: LLMRequest) -> LLMResponse:
        return make_mock_response(self._response)


class TestLLMResponse:
    def test_total_tokens(self):
        resp = make_mock_response()
        resp.input_tokens = 100
        resp.output_tokens = 50
        assert resp.total_tokens == 150


class TestLLMClient:
    def test_register_and_complete(self):
        client = LLMClient()
        client.register("mock", MockProvider("resposta"))

        request = LLMRequest(prompt="teste")
        response = client.complete("mock", request)

        assert response.content == "resposta"
        assert response.provider == "mock"

    def test_unknown_provider_raises(self):
        client = LLMClient()
        with pytest.raises(KeyError, match="nao_existe"):
            client.complete("nao_existe", LLMRequest(prompt="teste"))

    def test_compare_returns_all_providers(self):
        client = LLMClient()
        client.register("a", MockProvider("resp_a"))
        client.register("b", MockProvider("resp_b"))

        results = client.compare(LLMRequest(prompt="teste"))

        assert set(results.keys()) == {"a", "b"}
        assert results["a"].content == "resp_a"
        assert results["b"].content == "resp_b"

    def test_method_chaining_on_register(self):
        client = LLMClient()
        result = client.register("mock", MockProvider())
        assert result is client
