import logging
from typing import Any, Literal
from pydantic import BaseModel, Field

logger = logging.getLogger("alfaia.tools_registry")


# Schemas Pydantic das 8 Tools de PRD §8.2

class BuscarProdutosInput(BaseModel):
    evento: str | None = Field(None, description="Tipo de evento (ex: casamento, formatura)")
    estilo: str | None = Field(None, description="Estilo da peça (ex: longo, curto, sereia)")
    categoria: str | None = Field(None, description="Categoria do vestuário")
    cor: str | None = Field(None, description="Cor de preferência")
    tamanho: str | None = Field(None, description="Tamanho da peça (ex: 38, 40, 42)")
    data_inicio: str | None = Field(None, description="Data início do evento YYYY-MM-DD")
    data_fim: str | None = Field(None, description="Data fim do evento YYYY-MM-DD")
    q: str | None = Field(None, description="Termo livre de busca")


class ConsultarSlotsInput(BaseModel):
    tipo: str = Field(..., description="Tipo de agendamento (ex: prova, retirada, ajuste)")
    data_inicio: str = Field(..., description="Data início YYYY-MM-DD")
    data_fim: str | None = Field(None, description="Data fim YYYY-MM-DD")


class AgendarInput(BaseModel):
    tipo: str = Field(..., description="Tipo de agendamento (ex: prova, retirada, devolução)")
    data: str = Field(..., description="Data do agendamento YYYY-MM-DD")
    hora: str = Field(..., description="Horário do agendamento HH:MM")
    produto_ref: str | None = Field(None, description="Código ou referência da peça")
    observacao: str | None = Field(None, description="Observação adicional")


class AtualizarLeadInput(BaseModel):
    evento_tipo: str | None = None
    evento_data: str | None = None
    papel: str | None = None
    peca_interesse: str | None = None
    tamanho: str | None = None
    cor: str | None = None
    valor_estimado: float | None = None


class MoverStatusInput(BaseModel):
    status_destino: str = Field(..., description="Status destino no Kanban (ex: qualificando, orcamento, negociando, descartado)")
    motivo: str | None = Field(None, description="Motivo textual da movimentação (obrigatório para descarte)")


class RegistrarInteresseInput(BaseModel):
    evento_tipo: str | None = None
    evento_data: str | None = None
    papel: str | None = None
    peca_interesse: str | None = None
    tamanho: str | None = None
    cor: str | None = None
    valor_estimado: float | None = None


class AbrirTransbordoInput(BaseModel):
    motivo: str = Field(..., description="Motivo do transbordo humano (ex: solicitação explícita, assunto crítico, erro de API)")
    criticidade: Literal["baixa", "media", "alta"] = Field("media", description="Nível de criticidade do transbordo")


class EncerrarInput(BaseModel):
    desfecho: Literal["ganho", "descartado"] = Field(..., description="Desfecho do atendimento (ganho ou descartado)")
    motivo: str | None = Field(None, description="Motivo textual do encerramento")


class ToolsRegistry:
    """
    Registro Central e Execuror das 8 Ferramentas do Motor de IA (PRD §8.2, AC 5).
    """

    def __init__(self):
        self.ferramentas = {
            "buscar_produtos": self.buscar_produtos,
            "consultar_slots": self.consultar_slots,
            "agendar": self.agendar,
            "atualizar_lead": self.atualizar_lead,
            "mover_status": self.mover_status,
            "registrar_interesse": self.registrar_interesse,
            "abrir_transbordo": self.abrir_transbordo,
            "encerrar": self.encerrar,
        }

    def executar_tool(self, nome_tool: str, argumentos: dict[str, Any], contexto_execucao: dict[str, Any]) -> dict[str, Any]:
        if nome_tool not in self.ferramentas:
            logger.error(f"Tool desconhecida tentada pela IA: '{nome_tool}'")
            return {"sucesso": False, "erro": f"Ferramenta '{nome_tool}' não registrada."}

        func = self.ferramentas[nome_tool]
        try:
            return func(argumentos, contexto_execucao)
        except Exception as e:
            logger.error(f"Falha na execução da tool '{nome_tool}': {e}")
            return {"sucesso": False, "erro": str(e), "acao": "abrir_transbordo"}

    def buscar_produtos(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = BuscarProdutosInput(**args)
        tenant_id = ctx.get("tenant_id", "tenant_piloto")
        logger.info(f"Tool 'buscar_produtos' executada [params={params.model_dump(exclude_none=True)}]")

        from app.services.product_search_service import product_search_service
        return product_search_service.buscar_produtos_com_cache(
            tenant_id=tenant_id,
            params=params.model_dump(exclude_none=True),
        )

    def consultar_slots(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = ConsultarSlotsInput(**args)
        tenant_id = ctx.get("tenant_id", "tenant_piloto")
        logger.info(f"Tool 'consultar_slots' executada [params={params.model_dump()}]")

        from app.services.scheduling_service import scheduling_service
        return scheduling_service.consultar_slots(
            tenant_id=tenant_id,
            tipo=params.tipo,
            data_inicio=params.data_inicio,
            data_fim=params.data_fim,
        )

    def agendar(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = AgendarInput(**args)
        tenant_id = ctx.get("tenant_id", "tenant_piloto")
        lead = ctx.get("lead")
        lead_id = lead.id if lead else "lead_piloto"
        cliente_nome = lead.nome if hasattr(lead, "nome") and lead.nome else "Lead ALFAIA"
        cliente_telefone = lead.telefone if hasattr(lead, "telefone") and lead.telefone else "5585988112233"

        logger.info(f"Tool 'agendar' executada [params={params.model_dump()}]")

        from app.services.scheduling_service import scheduling_service
        return scheduling_service.agendar_prova_ou_retirada(
            tenant_id=tenant_id,
            lead_id=lead_id,
            tipo=params.tipo,
            data=params.data,
            hora=params.hora,
            cliente_nome=cliente_nome,
            cliente_telefone=cliente_telefone,
            produto_ref=params.produto_ref,
            observacao=params.observacao,
        )

    def atualizar_lead(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = AtualizarLeadInput(**args)
        lead = ctx.get("lead")
        if lead:
            for k, v in params.model_dump(exclude_none=True).items():
                setattr(lead, k, v)
        logger.info(f"Tool 'atualizar_lead' executada [params={params.model_dump(exclude_none=True)}]")
        return {"sucesso": True, "mensagem": "Dados do lead atualizados."}

    def mover_status(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = MoverStatusInput(**args)
        from app.services.status_transition_service import status_transition_service
        lead = ctx.get("lead")
        tenant_id = ctx.get("tenant_id", "tenant_piloto")
        lead_service = ctx.get("lead_service")

        if not lead:
            return {"sucesso": False, "erro": "Objeto lead ausente no contexto."}

        sucesso, msg = status_transition_service.validar_e_mover_status(
            tenant_id=tenant_id,
            lead=lead,
            status_destino=params.status_destino,
            autor="ia",
            motivo=params.motivo,
            lead_service=lead_service,
        )

        return {"sucesso": sucesso, "mensagem": msg}

    def registrar_interesse(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = RegistrarInteresseInput(**args)
        from app.services.interest_service import interest_service
        lead = ctx.get("lead")
        tenant_id = ctx.get("tenant_id", "tenant_piloto")
        lead_service = ctx.get("lead_service")

        if not lead or not lead_service:
            return {"sucesso": False, "erro": "Objeto lead/service ausente no contexto."}

        lead_resultante, registro, tipo = interest_service.processar_registro_interesse(
            tenant_id=tenant_id,
            lead_atual=lead,
            lead_service=lead_service,
            novo_interesse=params.model_dump(exclude_none=True),
        )

        return {
            "sucesso": True,
            "tipo_mudanca": tipo,
            "versao_interesse": registro.versao if registro else 1,
            "novo_lead_id": lead_resultante.id,
        }

    def abrir_transbordo(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = AbrirTransbordoInput(**args)
        conversa = ctx.get("conversa")
        if conversa:
            conversa["estado"] = "transbordo"
        logger.info(f"Tool 'abrir_transbordo' acionada [motivo={params.motivo}]")
        return {"sucesso": True, "estado": "transbordo", "mensagem": "Transbordo humano acionado."}

    def encerrar(self, args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        params = EncerrarInput(**args)
        if params.desfecho == "ganho":
            return {"sucesso": False, "erro": "MV1: A IA não pode encerrar como ganho. Apenas operador humano fecha contrato."}

        return self.mover_status({"status_destino": "descartado", "motivo": params.motivo or "Encerramento via IA"}, ctx)


tools_registry = ToolsRegistry()
