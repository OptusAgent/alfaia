import os
import time
import logging
from typing import Any
from pydantic import BaseModel, Field

from app.services.supabase_rest import supabase_rest_service

logger = logging.getLogger("alfaia.weblocacao")

# Bucket público (`wl-mock-catalogo`) com as fotos reais do catálogo de desenvolvimento — usa
# SUPABASE_URL do ambiente para não fixar o projeto no código (story 4.9).
_SUPABASE_URL = os.getenv("SUPABASE_URL", "https://irewoqkwywsapiiytdau.supabase.co").rstrip("/")


def _url_imagem_mock(arquivo: str) -> str:
    return f"{_SUPABASE_URL}/storage/v1/object/public/wl-mock-catalogo/{arquivo}"


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
    # Lista real de tamanhos em estoque (story 4.9, follow-up) — `tamanho` continua existindo
    # (junção legível dos mesmos valores) para não quebrar nenhum consumidor já existente.
    tamanhos_disponiveis: list[str] = []


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


class WLAgendaItemDTO(BaseModel):
    """Item de GET /agenda (§7.2) — agendamento visto do lado do ERP, origem loja ou automação."""
    id: str
    tipo: str
    data: str
    hora: str
    cliente_nome: str
    cliente_telefone: str
    produto: str | None = None
    origem: str = "loja"


class WLException(Exception):
    """Exceção customizada para erros de integração WebLocação."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code



# Catálogo sintético completo (9 peças reais, mesmo conjunto de imagens do bucket
# `wl-mock-catalogo` e do `wl-fake-api` — story 4.9, follow-up 2026-08-21). Achado real: o mock
# anterior devolvia sempre os mesmos 2 vestidos hardcoded independente do filtro pedido (um lead
# pedindo "terno" recebia foto/dados de vestido) — corrigido para filtrar categoria/evento/cor/
# tamanho de verdade contra um catálogo com peças distintas.
_CATALOGO_MOCK: list[dict[str, Any]] = [
    {"id": "wl_p101", "ref": "V-101", "nome": "Vestido Aurora Tomara-que-Caia", "categoria": "casamento/noiva",
     "cor": "Off-White", "estilo": "Princesa (A-line)", "valor_aluguel": 890.0, "arquivo": "noiva001.jpg",
     "tamanhos": ["36", "38", "40", "42"]},
    {"id": "wl_p102", "ref": "V-102", "nome": "Vestido Elise Sereia Ombro a Ombro", "categoria": "casamento/noiva",
     "cor": "Marfim", "estilo": "Sereia", "valor_aluguel": 1050.0, "arquivo": "noiva002.jpg",
     "tamanhos": ["36", "38", "40", "42"]},
    {"id": "wl_p201", "ref": "T-201", "nome": "Terno Marinho Slim 3 Peças", "categoria": "casamento/traje-masculino",
     "cor": "Azul Marinho", "estilo": "Slim, 3 peças", "valor_aluguel": 420.0, "arquivo": "0002.jpeg",
     "tamanhos": ["46", "48", "50", "52"]},
    {"id": "wl_p202", "ref": "T-202", "nome": "Terno Areia Rústico 3 Peças", "categoria": "casamento/traje-masculino",
     "cor": "Bege Areia", "estilo": "Rústico, 3 peças", "valor_aluguel": 450.0, "arquivo": "TERNOMASCULINO001.jpg",
     "tamanhos": ["46", "48", "52"]},
    {"id": "wl_p203", "ref": "T-203", "nome": "Terno Linho Praia Champanhe", "categoria": "casamento/traje-masculino",
     "cor": "Bege Claro", "estilo": "Linho", "valor_aluguel": 460.0, "arquivo": "TERNOMASCULINO002.jpg",
     "tamanhos": ["46", "48", "50"]},
    {"id": "wl_p204", "ref": "T-204", "nome": "Terno Marinho Clássico Social", "categoria": "casamento/traje-masculino",
     "cor": "Azul Marinho", "estilo": "Clássico Social", "valor_aluguel": 480.0, "arquivo": "TERNOMASCULINO003.jpg",
     "tamanhos": ["46", "48", "50", "52"]},
    {"id": "wl_p301", "ref": "F-301", "nome": "Vestido Noite Preto Plissado", "categoria": "festa/madrinha",
     "cor": "Preto", "estilo": "Plissado", "valor_aluguel": 380.0, "arquivo": "VESTIDO01.jpg",
     "tamanhos": ["36", "38", "40"]},
    {"id": "wl_p302", "ref": "F-302", "nome": "Vestido Festa Laranja Costas Abertas", "categoria": "festa/madrinha",
     "cor": "Laranja", "estilo": "Costas Abertas", "valor_aluguel": 350.0, "arquivo": "VESTIDO02.jpg",
     "tamanhos": ["36", "38", "40", "42"]},
    {"id": "wl_p303", "ref": "F-303", "nome": "Vestido Esmeralda Um Ombro Só", "categoria": "festa/madrinha",
     "cor": "Verde Esmeralda", "estilo": "Um Ombro Só", "valor_aluguel": 360.0, "arquivo": "VESTIDO03.jpg",
     "tamanhos": ["40", "42", "44", "46"]},
]

# Sinônimos livres que a IA pode mandar em `categoria` -> segmento(s) real(is) da categoria
# cadastrada. Sem isso, "terno"/"smoking" nunca bateria com "traje-masculino" e o filtro
# devolveria vazio (ou, no bug antigo, ignorava o filtro por completo).
_SINONIMOS_CATEGORIA: dict[str, list[str]] = {
    "terno": ["traje-masculino"], "ternos": ["traje-masculino"], "smoking": ["traje-masculino"],
    "traje": ["traje-masculino"], "traje-masculino": ["traje-masculino"], "masculino": ["traje-masculino"],
    "noiva": ["noiva"], "vestido de noiva": ["noiva"],
    "madrinha": ["madrinha"], "festa": ["madrinha"],
    "vestido": ["noiva", "madrinha"], "vestidos": ["noiva", "madrinha"],
}


class WLMockAdapter:
    """
    Adaptador Mock Obrigatório cumprindo rigorosamente o contrato de PRD §7.2 (I8).
    """

    def buscar_produtos(self, params: dict[str, Any]) -> list[WLProdutoDTO]:
        evento = str(params.get("evento") or "").strip().lower()
        categoria_in = str(params.get("categoria") or "").strip().lower()
        cor_in = str(params.get("cor") or "").strip().lower()
        tamanho_in = str(params.get("tamanho") or "").strip()
        # Busca livre (`q`) ignorada até aqui — quando o lead menciona um código/nome específico
        # já visto (ex.: "sim o T-203"), a IA manda esse termo em `q`, mas sem filtrar por ele o
        # mock devolvia o mesmo grupo inteiro de novo, parecendo repetir a lista (achado real em
        # produção, 2026-08-21).
        q_in = str(params.get("q") or "").strip().lower()

        segmentos_alvo = _SINONIMOS_CATEGORIA.get(categoria_in) if categoria_in else None

        encontrados = []
        for item in _CATALOGO_MOCK:
            if evento and not item["categoria"].startswith(evento):
                continue
            if segmentos_alvo and not any(seg in item["categoria"] for seg in segmentos_alvo):
                continue
            if cor_in and cor_in not in item["cor"].lower():
                continue
            if tamanho_in and tamanho_in not in item["tamanhos"]:
                continue
            if q_in and q_in not in item["ref"].lower() and q_in not in item["nome"].lower():
                continue
            encontrados.append(
                WLProdutoDTO(
                    id=item["id"],
                    ref=item["ref"],
                    nome=item["nome"],
                    categoria=item["categoria"],
                    tamanho=", ".join(item["tamanhos"]),
                    cor=item["cor"],
                    estilo=item["estilo"],
                    valor_aluguel=item["valor_aluguel"],
                    disponivel=True,
                    imagem=_url_imagem_mock(item["arquivo"]),
                    tamanhos_disponiveis=list(item["tamanhos"]),
                )
            )
        return encontrados

    def obter_produto(self, produto_id: str) -> WLProdutoDTO:
        item = next((i for i in _CATALOGO_MOCK if i["id"] == produto_id), _CATALOGO_MOCK[0])
        return WLProdutoDTO(
            id=item["id"],
            ref=item["ref"],
            nome=item["nome"],
            categoria=item["categoria"],
            tamanho=", ".join(item["tamanhos"]),
            cor=item["cor"],
            estilo=item["estilo"],
            valor_aluguel=item["valor_aluguel"],
            disponivel=True,
            imagem=_url_imagem_mock(item["arquivo"]),
            tamanhos_disponiveis=list(item["tamanhos"]),
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

    def listar_agendamentos(self, data_inicio: str, data_fim: str | None = None) -> list[WLAgendaItemDTO]:
        """
        Mock de GET /agenda (§7.2) — agendamentos feitos direto no balcão da loja (origem='loja').
        Datas fixas (não derivadas de data_inicio/data_fim) para simular reservas reais já existentes
        no ERP, na mesma linha do fixture usado pela story 5.4/5.6.
        """
        return [
            WLAgendaItemDTO(
                id="wl_ag_loja_01",
                tipo="prova",
                data="2026-09-05",
                hora="10:00",
                cliente_nome="Fernanda Alencar",
                cliente_telefone="5585999887766",
                produto="V-101",
                origem="loja",
            ),
            WLAgendaItemDTO(
                id="wl_ag_loja_02",
                tipo="retirada",
                data="2026-09-12",
                hora="15:00",
                cliente_nome="Juliana Paes",
                cliente_telefone="5585988776655",
                produto="T-201",
                origem="loja",
            ),
        ]


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
        Registra telemétrica de chamadas à API da WebLocação em wl_chamadas (I3, story 5.6 AC 1).
        Grava em Postgres via `supabase_rest_service` (no-op silencioso se não configurado — ex.:
        testes sem credencial). `chamadas_log` em memória é mantido só como espelho local rápido,
        não é mais a fonte de verdade.
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
        try:
            supabase_rest_service.registrar_wl_chamada(tenant_id, metodo, rota, status_code, latencia_ms, erro)
        except Exception as e:
            # Auditoria não pode nunca derrubar a chamada real ao WL nem a resposta ao lead (I2, P3, AC 4)
            logger.warning(f"Falha inesperada ao registrar wl_chamadas (nao bloqueante): {e}")

    def buscar_produtos(self, tenant_id: str = "tenant_piloto", **params) -> list[WLProdutoDTO]:
        modo = self._obter_modo()
        t0 = time.time()

        if modo == "mock":
            res = self.mock_adapter.buscar_produtos(params)
            latencia = int((time.time() - t0) * 1000)
            self.registrar_chamada(tenant_id, "GET", "/produtos", 200, latencia)
            return res

        brutos = self._chamar_api_real(tenant_id, "GET", "/produtos", t0, params=params)
        # Tradução da camada anticorrupção (I7, AC 2)
        return [self._traduzir_produto(item) for item in brutos]

    def obter_produto(self, produto_id: str, tenant_id: str = "tenant_piloto") -> WLProdutoDTO:
        modo = self._obter_modo()
        t0 = time.time()

        if modo == "mock":
            res = self.mock_adapter.obter_produto(produto_id)
            latencia = int((time.time() - t0) * 1000)
            self.registrar_chamada(tenant_id, "GET", f"/produtos/{produto_id}", 200, latencia)
            return res

        bruto = self._chamar_api_real(tenant_id, "GET", f"/produtos/{produto_id}", t0)
        return self._traduzir_produto(bruto)

    def consultar_slots(self, tenant_id: str = "tenant_piloto", tipo: str = "prova", data_inicio: str = "2026-09-01") -> list[WLSlotDTO]:
        modo = self._obter_modo()
        t0 = time.time()

        if modo == "mock":
            res = self.mock_adapter.consultar_slots(tipo, data_inicio)
            latencia = int((time.time() - t0) * 1000)
            self.registrar_chamada(tenant_id, "GET", "/agenda/slots", 200, latencia)
            return res

        brutos = self._chamar_api_real(
            tenant_id, "GET", "/agenda/slots", t0, params={"tipo": tipo, "data_inicio": data_inicio}
        )
        return [
            WLSlotDTO(
                data=item["data"],
                hora=item["hora"],
                vagas_totais=item["vagas_totais"],
                vagas_livres=item["vagas_livres"],
            )
            for item in brutos
        ]

    def criar_agendamento(self, tenant_id: str = "tenant_piloto", **dados) -> WLAgendamentoDTO:
        modo = self._obter_modo()
        t0 = time.time()

        if modo == "mock":
            res = self.mock_adapter.criar_agendamento(dados)
            latencia = int((time.time() - t0) * 1000)
            self.registrar_chamada(tenant_id, "POST", "/agenda", 201, latencia)
            return res

        bruto = self._chamar_api_real(tenant_id, "POST", "/agenda", t0, json_body=dados)
        return WLAgendamentoDTO(
            id=bruto["id"],
            status=bruto["status"],
            tipo=dados.get("tipo", "prova"),
            data=dados.get("data", ""),
            hora=dados.get("hora", ""),
            cliente_nome=dados.get("cliente_nome", ""),
            cliente_telefone=dados.get("cliente_telefone", ""),
            produto_id=dados.get("produto_id"),
            observacao=dados.get("observacao"),
        )

    def listar_agendamentos(
        self, tenant_id: str = "tenant_piloto", data_inicio: str = "2026-09-01", data_fim: str | None = None
    ) -> list[WLAgendaItemDTO]:
        """
        GET /agenda (§7.2) — agendamentos vistos do lado do ERP, para a sincronização de agenda
        distinguir origem='loja' vs 'automacao' (story 5.4 AC 11.2/11.3, story 5.6 AC 3).
        """
        modo = self._obter_modo()
        t0 = time.time()

        if modo == "mock":
            res = self.mock_adapter.listar_agendamentos(data_inicio, data_fim)
            latencia = int((time.time() - t0) * 1000)
            self.registrar_chamada(tenant_id, "GET", "/agenda", 200, latencia)
            return res

        brutos = self._chamar_api_real(
            tenant_id, "GET", "/agenda", t0, params={"data_inicio": data_inicio, "data_fim": data_fim}
        )
        return [
            WLAgendaItemDTO(
                id=item["id"],
                tipo=item["tipo"],
                data=item["data"],
                hora=item["hora"],
                cliente_nome=item["cliente_nome"],
                cliente_telefone=item["cliente_telefone"],
                produto=item.get("produto"),
                origem=item.get("origem", "loja"),
            )
            for item in brutos
        ]

    @staticmethod
    def _traduzir_produto(item: dict[str, Any]) -> WLProdutoDTO:
        """Camada anticorrupção: nenhum campo cru do ERP (codigo, valor_locacao, status) vaza (I7)."""
        return WLProdutoDTO(
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

    def _chamar_api_real(
        self,
        tenant_id: str,
        metodo: str,
        rota: str,
        t0: float,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """
        Cliente HTTP real com timeout 8s e retry 2x em 5xx, sem retry em 4xx (I2, I4, AC 4, AC 5).
        Usado por todas as rotas do contrato §7.2 quando `WL_MODO=real`.
        """
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
                    if metodo == "GET":
                        resp = client.get(f"{base_url}{rota}", headers=headers, params=params)
                    else:
                        resp = client.post(f"{base_url}{rota}", headers=headers, json=json_body)

                    latencia = int((time.time() - t0) * 1000)

                    if 200 <= resp.status_code < 300:
                        self.registrar_chamada(tenant_id, metodo, rota, resp.status_code, latencia)
                        return resp.json()
                    elif resp.status_code >= 500 and attempts <= max_retries_5xx:
                        logger.warning(f"Erro 5xx na API WL (rota={rota}, tentativa {attempts}). Retentando...")
                        time.sleep(0.5 * attempts)
                        continue
                    else:
                        # 4xx sem retry (I4)
                        self.registrar_chamada(tenant_id, metodo, rota, resp.status_code, latencia, erro=resp.text)
                        raise WLException(f"Erro da API WebLocação: status {resp.status_code}", status_code=resp.status_code)
            except httpx.TimeoutException:
                latencia = int((time.time() - t0) * 1000)
                self.registrar_chamada(tenant_id, metodo, rota, 504, latencia, erro="Timeout 8s excedido")
                raise WLException("Timeout de 8s excedido na API da WebLocação.", status_code=504)
            except WLException:
                raise
            except Exception as e:
                latencia = int((time.time() - t0) * 1000)
                self.registrar_chamada(tenant_id, metodo, rota, 500, latencia, erro=str(e))
                raise WLException(f"Falha de conexão com a WebLocação: {e}", status_code=500)

        raise WLException("Falha crítica de comunicação com a WebLocação após retries.", status_code=500)


weblocacao_service = WebLocacaoService()
