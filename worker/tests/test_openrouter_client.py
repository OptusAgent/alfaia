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

    assert resposta == "Resposta real do modelo via mock."


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
