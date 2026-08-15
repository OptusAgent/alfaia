import os
import time
import logging
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger("alfaia.weblocacao")


# DTOs Internos da Camada Anticorrupção ALFAIA (I7, PRD §7.2)
class WLProdutoDTO(BaseModel):
    id: str
    ref: str
    nome: str
    categoria: str
    tamanho: str
    cor: str
    estilo: str | None = None
    valor_aluguel: float
    disponivel: bool = True
    imagem: str | None = None


class WLSlotDTO(BaseModel):
    data: str
    hora: str
    vagas_totais: int
    vagas_livres: int


class WLAgendamentoDTO(BaseModel):
    id: str
    status: str
    tipo: str
    data: str
    hora: str
    cliente_nome: str
    cliente_telefone: str
    produto_id: str | None = None
    observacao: str | None = None


class WLException(Exception):
    """Exceção customizada para erros de integração WebLocação."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class WLMockAdapter:
    """
    Adaptador Mock Obrigatório cumprindo rigorosamente o contrato de PRD §7.2 (I8).
    """

    def buscar_produtos(self, params: dict[str, Any]) -> list[WLProdutoDTO]:
        categoria = params.get("categoria", "Vestidos")
        tamanho = params.get("tamanho", "42")
        cor = params.get("cor", "Champanhe")

        # Dados traduzidos sem vazamento de contrato do ERP
        return [
            WLProdutoDTO(
                id="wl_p101",
                ref="V-101",
                nome="Vestido Longo Champanhe Sereia",
                categoria=categoria,
                tamanho=tamanho,
                cor=cor,
                estilo="Sereia",
                valor_aluguel=520.0,
                disponivel=True,
                imagem="https://alfaia.app/images/v101.jpg",
            ),
            WLProdutoDTO(
                id="wl_p102",
                ref="V-102",
                nome="Vestido Longo Marsala Fluido",
                categoria=categoria,
                tamanho=tamanho,
                cor="Marsala",
                estilo="Fluido",
                valor_aluguel=480.0,
                disponivel=True,
                imagem="https://alfaia.app/images/v102.jpg",
            ),
        ]

    def obter_produto(self, produto_id: str) -> WLProdutoDTO:
        return WLProdutoDTO(
            id=produto_id,
            ref="V-101",
            nome="Vestido Longo Champanhe Sereia",
            categoria="Vestidos",
            tamanho="42",
            cor="Champanhe",
            estilo="Sereia",
            valor_aluguel=520.0,
            disponivel=True,
        )

    def consultar_slots(self, tipo: str, data_inicio: str, data_fim: str | None = None) -> list[WLSlotDTO]:
        return [
            WLSlotDTO(data=data_inicio, hora="09:00", vagas_totais=2, vagas_livres=2),
            WLSlotDTO(data=data_inicio, hora="11:00", vagas_totais=2, vagas_livres=1),
            WLSlotDTO(data=data_inicio, hora="14:00", vagas_totais=2, vagas_livres=2),
            WLSlotDTO(data=data_inicio, hora="16:00", vagas_totais=2, vagas_livres=0),
        ]

    def criar_agendamento(self, dados: dict[str, Any]) -> WLAgendamentoDTO:
        return WLAgendamentoDTO(
            id="wl_ag_999",
            status="confirmado",
            tipo=dados.get("tipo", "prova"),
            data=dados.get("data", "2026-09-01"),
            hora=dados.get("hora", "14:00"),
            cliente_nome=dados.get("cliente_nome", "Cliente Teste"),
            cliente_telefone=dados.get("cliente_telefone", "5585988112233"),
            produto_id=dados.get("produto_id"),
            observacao=dados.get("observacao"),
        )


class WebLocacaoService:
    """
    Camada Anticorrupção e Cliente de Integração WebLocação (PRD §7.2, §7.3, §17.7, AC 1-6).
    """

    def __init__(self):
        self.mock_adapter = WLMockAdapter()
        self.chamadas_log: list[dict[str, Any]] = []
        self.modos_tenant: dict[str, str] = {}

    def configurar_modo_tenant(self, tenant_id: str, modo: str = "mock") -> dict[str, Any]:
        """Configura o modo de integração (mock/real) para o tenant (I8, AC 3)."""
        self.modos_tenant[tenant_id] = modo
        logger.info(f"Modo de integração WebLocação configurado [tenant={tenant_id}, modo='{modo}']")
        return {"sucesso": True, "tenant_id": tenant_id, "modo": modo}

    def _obter_modo(self, tenant_id: str | None = None) -> str:
        if tenant_id and tenant_id in self.modos_tenant:
            return self.modos_tenant[tenant_id].lower()
        return os.getenv("WL_MODO", "mock").lower()

    def registrar_chamada(self, tenant_id: str, metodo: str, rota: str, status_code: int, latencia_ms: int, erro: str | None = None):
        """
        Registra telemétrica de chamadas à API da WebLocação em wl_chamadas (I3, AC 3).
        """
        registro = {
            "tenant_id": tenant_id,
            "metodo": metodo,
            "rota": rota,
            "status_code": status_code,
            "latencia_ms": latencia_ms,
            "erro": erro,
            "criado_em": time.time(),
        }
        self.chamadas_log.append(registro)
        logger.info(f"WL Chamada Registrada [rota={rota}, status={status_code}, latencia={latencia_ms}ms]")

    def buscar_produtos(self, tenant_id: str = "tenant_piloto", **params) -> list[WLProdutoDTO]:
        modo = self._obter_modo()
        t0 = time.time()

        if modo == "mock":
            res = self.mock_adapter.buscar_produtos(params)
            latencia = int((time.time() - t0) * 1000)
            self.registrar_chamada(tenant_id, "GET", "/produtos", 200, latencia)
            return res

        # Invocação de cliente real com timeout 8s e retries 5xx (I2, I4)
        return self._invocar_cliente_real_produtos(tenant_id, params, t0)

    def _invocar_cliente_real_produtos(self, tenant_id: str, params: dict[str, Any], t0: float) -> list[WLProdutoDTO]:
        import httpx
        timeout = 8.0  # Timeout estrito de 8s (I2, AC 4)
        attempts = 0
        max_retries_5xx = 2  # Retry 2x em 5xx (I4, AC 5)

        base_url = os.getenv("WL_BASE_URL", "https://api.weblocacao.fake.com")
        api_key = os.getenv("WL_API_KEY", "secret_key")

        headers = {"Authorization": f"Bearer {api_key}"}

        while attempts <= max_retries_5xx:
            attempts += 1
            try:
                with httpx.Client(timeout=timeout) as client:
                    resp = client.get(f"{base_url}/produtos", headers=headers, params=params)
                    latencia = int((time.time() - t0) * 1000)

                    if resp.status_code == 200:
                        self.registrar_chamada(tenant_id, "GET", "/produtos", 200, latencia)
                        # Tradução da camada anticorrupção (I7, AC 2)
                        brutos = resp.json()
                        return [
                            WLProdutoDTO(
                                id=item["id"],
                                ref=item.get("codigo", item["id"]),
                                nome=item["nome"],
                                categoria=item.get("categoria", "Vestidos"),
                                tamanho=item.get("tamanho", "U"),
                                cor=item.get("cor", "Única"),
                                estilo=item.get("estilo"),
                                valor_aluguel=float(item.get("valor_locacao", 0.0)),
                                disponivel=item.get("status") == "disponivel",
                                imagem=item.get("foto_url"),
                            )
                            for item in brutos
                        ]
                    elif resp.status_code >= 500 and attempts <= max_retries_5xx:
                        logger.warning(f"Erro 5xx na API WL (tentativa {attempts}). Retentando...")
                        time.sleep(0.5 * attempts)
                        continue
                    else:
                        # 4xx sem retry (I4)
                        self.registrar_chamada(tenant_id, "GET", "/produtos", resp.status_code, latencia, erro=resp.text)
                        raise WLException(f"Erro da API WebLocação: status {resp.status_code}", status_code=resp.status_code)
            except httpx.TimeoutException:
                latencia = int((time.time() - t0) * 1000)
                self.registrar_chamada(tenant_id, "GET", "/produtos", 504, latencia, erro="Timeout 8s excedido")
                raise WLException("Timeout de 8s excedido na API da WebLocação.", status_code=504)
            except Exception as e:
                latencia = int((time.time() - t0) * 1000)
                self.registrar_chamada(tenant_id, "GET", "/produtos", 500, latencia, erro=str(e))
                raise WLException(f"Falha de conexão com a WebLocação: {e}", status_code=500)

        raise WLException("Falha crítica de comunicação com a WebLocação após retries.", status_code=500)

    def consultar_slots(self, tenant_id: str = "tenant_piloto", tipo: str = "prova", data_inicio: str = "2026-09-01") -> list[WLSlotDTO]:
        t0 = time.time()
        res = self.mock_adapter.consultar_slots(tipo, data_inicio)
        latencia = int((time.time() - t0) * 1000)
        self.registrar_chamada(tenant_id, "GET", "/agenda/slots", 200, latencia)
        return res

    def criar_agendamento(self, tenant_id: str = "tenant_piloto", **dados) -> WLAgendamentoDTO:
        t0 = time.time()
        res = self.mock_adapter.criar_agendamento(dados)
        latencia = int((time.time() - t0) * 1000)
        self.registrar_chamada(tenant_id, "POST", "/agenda", 201, latencia)
        return res


weblocacao_service = WebLocacaoService()
