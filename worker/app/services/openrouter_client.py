import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("alfaia.openrouter_client")


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
        mensagens: list[dict[str, str]],
        temperatura: float = 0.3,
    ) -> str | None:
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

            content = choices[0].get("message", {}).get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()

            logger.error("OpenRouter retornou conteudo vazio.")
            return None
        except Exception as exc:
            logger.error("Falha ao chamar OpenRouter: %s", exc, exc_info=True)
            return None


openrouter_client = OpenRouterClient()
