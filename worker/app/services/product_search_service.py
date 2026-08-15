import time
import json
import logging
from typing import Any

from app.services.weblocacao_service import weblocacao_service, WLProdutoDTO

logger = logging.getLogger("alfaia.product_search")


class ProductSearchService:
    """
    Serviço de Busca, Ranqueamento e Caching Transitório de Produtos (PRD §12, AC 1-4).
    - Cache em memória TTL 60s (Decisão A4, AC 4).
    - Ranqueamento e corte em no máximo 5 itens (AC 12.2).
    - Resposta graciosa para 0 itens sem inventar dados (Princípio P3, AC 12.3).
    """

    def __init__(self, ttl_segundos: float = 60.0):
        self.ttl_segundos = ttl_segundos
        # Cache em memória: key -> (timestamp_expiracao, list[WLProdutoDTO])
        self._cache: dict[str, tuple[float, list[WLProdutoDTO]]] = {}

    def _gerar_chave_cache(self, tenant_id: str, params: dict[str, Any]) -> str:
        params_str = json.dumps(params, sort_keys=True, default=str)
        return f"{tenant_id}:{params_str}"

    def buscar_produtos_com_cache(
        self,
        tenant_id: str = "tenant_piloto",
        params: dict[str, Any] | None = None,
        now: float | None = None,
    ) -> dict[str, Any]:
        simulated_now = now if now is not None else time.time()
        filter_params = params or {}
        cache_key = self._gerar_chave_cache(tenant_id, filter_params)

        # 1. Verifica cache em memória (TTL 60s - Decisão A4, AC 4)
        if cache_key in self._cache:
            expiracao, itens_cached = self._cache[cache_key]
            if simulated_now < expiracao:
                logger.info(f"Busca de produtos retornada via CACHE (TTL 60s) [key={cache_key}]")
                return self._formatar_resposta(itens_cached)

        # 2. Invocação via camada anticorrupção WebLocação (Story 5.1)
        try:
            todos_produtos = weblocacao_service.buscar_produtos(tenant_id=tenant_id, **filter_params)
        except Exception as e:
            logger.error(f"Erro na busca de produtos WL: {e}")
            return {
                "sucesso": False,
                "produtos": [],
                "erro": str(e),
                "acao": "abrir_transbordo",
                "mensagem": "Não consegui verificar o catálogo no momento. Vou confirmar com nossa equipe.",
            }

        # 3. Ranqueamento e corte estrito em no máximo 5 itens (AC 2, AC 12.2)
        produtos_ranqueados = self._ranquear_e_limitar(todos_produtos, limite=5)

        # 4. Atualiza o cache em memória
        self._cache[cache_key] = (simulated_now + self.ttl_segundos, produtos_ranqueados)

        return self._formatar_resposta(produtos_ranqueados)

    def _ranquear_e_limitar(self, produtos: list[WLProdutoDTO], limite: int = 5) -> list[WLProdutoDTO]:
        # Ordena prioritariamente por disponibilidade e por id
        produtos_ordenados = sorted(produtos, key=lambda p: (not p.disponivel, p.id))
        return produtos_ordenados[:limite]

    def _formatar_resposta(self, produtos: list[WLProdutoDTO]) -> dict[str, Any]:
        if not produtos:
            # AC 3, AC 12.3, P3: Resposta de indisponibilidade com sugestão de alternativa sem inventar dados
            return {
                "sucesso": True,
                "produtos": [],
                "quantidade": 0,
                "mensagem": "No momento não temos este modelo disponível para os filtros selecionados. Que tal darmos uma olhada em outros estilos ou ajustar a data do evento?",
            }

        return {
            "sucesso": True,
            "produtos": [p.model_dump() for p in produtos],
            "quantidade": len(produtos),
            "mensagem": f"Encontramos {len(produtos)} opções incríveis disponíveis para o seu evento.",
        }

    def limpar_cache(self):
        self._cache.clear()


product_search_service = ProductSearchService()
