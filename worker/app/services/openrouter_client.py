import json
import logging
import os
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger("alfaia.openrouter_client")


class LLMToolCallDTO(BaseModel):
    """Uma chamada de tool decidida pelo modelo (formato function-calling OpenAI/OpenRouter)."""
    id: str
    nome: str
    argumentos: dict[str, Any]


class LLMRespostaDTO(BaseModel):
    """
    Resposta de uma chamada ao LLM: texto final OU uma ou mais tool_calls a executar antes de
    haver texto final (story 4.8, AC 1). Nunca as duas coisas com conteúdo real ao mesmo tempo,
    seguindo o protocolo de function-calling.
    """
    content: str | None = None
    tool_calls: list[LLMToolCallDTO] = []


class OpenRouterClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
        httpx_client: httpx.Client | None = None,
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self._client = httpx_client

    @property
    def configurado(self) -> bool:
        return bool(self.api_key)

    def gerar_resposta(
        self,
        *,
        modelo: str,
        prompt_sistema: str,
        mensagens: list[dict[str, Any]],
        temperatura: float = 0.3,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMRespostaDTO | None:
        """
        Chama a API de chat completion da OpenRouter. Quando `tools` é passado (story 4.8, AC 1),
        o modelo pode responder com `tool_calls` em vez de texto — o chamador decide o que fazer
        com cada um (nunca esta função: ela só traduz a resposta bruta da API).
        """
        if not self.configurado:
            logger.warning("OpenRouter nao configurado: OPENROUTER_API_KEY ausente.")
            return None

        payload: dict[str, Any] = {
            "model": modelo,
            "temperature": temperatura,
            "messages": [
                {"role": "system", "content": prompt_sistema},
                *mensagens,
            ],
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://alfaia.app"),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "ALFAIA"),
        }

        try:
            if self._client:
                res = self._client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=45)
            else:
                with httpx.Client(timeout=45) as client:
                    res = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)

            if res.status_code not in (200, 201):
                logger.error("OpenRouter retornou HTTP %s: %s", res.status_code, res.text[:500])
                return None

            data = res.json()
            choices = data.get("choices") or []
            if not choices:
                logger.error("OpenRouter retornou sem choices.")
                return None

            mensagem = choices[0].get("message", {}) or {}
            tool_calls_brutas = mensagem.get("tool_calls") or []

            if tool_calls_brutas:
                tool_calls = []
                for tc in tool_calls_brutas:
                    funcao = tc.get("function", {}) or {}
                    try:
                        argumentos = json.loads(funcao.get("arguments") or "{}")
                    except json.JSONDecodeError:
                        logger.error("OpenRouter retornou argumentos de tool_call invalidos: %s", funcao.get("arguments"))
                        argumentos = {}
                    tool_calls.append(
                        LLMToolCallDTO(id=tc.get("id", ""), nome=funcao.get("name", ""), argumentos=argumentos)
                    )
                return LLMRespostaDTO(content=None, tool_calls=tool_calls)

            content = mensagem.get("content")
            if isinstance(content, str) and content.strip():
                return LLMRespostaDTO(content=content.strip(), tool_calls=[])

            logger.error("OpenRouter retornou sem conteudo e sem tool_calls.")
            return None
        except Exception as exc:
            logger.error("Falha ao chamar OpenRouter: %s", exc, exc_info=True)
            return None


openrouter_client = OpenRouterClient()
