import httpx

from app.services.openrouter_client import OpenRouterClient


def test_openrouter_client_reads_env_and_posts_completion(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-openrouter")
    monkeypatch.setenv("OPENROUTER_SITE_URL", "https://portal.alfaia.test")
    monkeypatch.setenv("OPENROUTER_APP_NAME", "ALFAIA QA")

    def handler(request: httpx.Request):
        assert request.method == "POST"
        assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer sk-test-openrouter"
        assert request.headers["HTTP-Referer"] == "https://portal.alfaia.test"
        assert request.headers["X-Title"] == "ALFAIA QA"

        body = request.read().decode("utf-8")
        assert '"model":"openai/gpt-4o-mini"' in body
        assert '"role":"system"' in body
        assert '"role":"user"' in body
        assert '"tools"' not in body  # sem tools passadas, nao deve mandar o campo (AC 1)

        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "Resposta real do modelo via mock."}}
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = OpenRouterClient(httpx_client=http_client)
        resposta = client.gerar_resposta(
            modelo="openai/gpt-4o-mini",
            prompt_sistema="Prompt sistema QA",
            mensagens=[{"role": "user", "content": "Oi"}],
            temperatura=0.2,
        )

    assert resposta.content == "Resposta real do modelo via mock."
    assert resposta.tool_calls == []


def test_openrouter_client_without_api_key_does_not_call_http(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def handler(request: httpx.Request):
        raise AssertionError("OpenRouter nao deveria ser chamado sem API key.")

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = OpenRouterClient(httpx_client=http_client)
        resposta = client.gerar_resposta(
            modelo="openai/gpt-4o-mini",
            prompt_sistema="Prompt sistema QA",
            mensagens=[{"role": "user", "content": "Oi"}],
        )

    assert resposta is None


def test_openrouter_client_envia_tools_e_traduz_tool_calls(monkeypatch):
    """Story 4.8, AC 1: com `tools`, o payload leva tools/tool_choice e a resposta traduz tool_calls."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-openrouter")

    tools = [
        {
            "type": "function",
            "function": {"name": "buscar_produtos", "description": "...", "parameters": {"type": "object", "properties": {}}},
        }
    ]

    def handler(request: httpx.Request):
        body = request.read().decode("utf-8")
        assert '"tools"' in body
        assert '"tool_choice":"auto"' in body

        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "function": {
                                        "name": "buscar_produtos",
                                        "arguments": '{"evento": "casamento", "tamanho": "42"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = OpenRouterClient(httpx_client=http_client)
        resposta = client.gerar_resposta(
            modelo="openai/gpt-4o-mini",
            prompt_sistema="Prompt sistema QA",
            mensagens=[{"role": "user", "content": "Quero um vestido de casamento"}],
            tools=tools,
        )

    assert resposta.content is None
    assert len(resposta.tool_calls) == 1
    assert resposta.tool_calls[0].nome == "buscar_produtos"
    assert resposta.tool_calls[0].argumentos == {"evento": "casamento", "tamanho": "42"}
