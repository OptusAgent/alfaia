import logging
from datetime import datetime, timedelta
from typing import Literal, Any
from pydantic import BaseModel, Field

logger = logging.getLogger("alfaia.lead_service")

TipoEntrada = Literal["primeiro_contato", "continuacao", "retomada", "reengajamento"]


class ContatoModel(BaseModel):
    id: str
    tenant_id: str
    telefone: str
    nome: str | None = None
    opt_out: bool = False
    tags: list[str] = Field(default_factory=list)
    total_leads: int = 0
    primeiro_contato_em: datetime = Field(default_factory=datetime.now)
    ultimo_contato_em: datetime = Field(default_factory=datetime.now)


class LeadModel(BaseModel):
    id: str
    tenant_id: str
    contato_id: str
    lead_seq: int = 1
    status: str = "novo"
    origem: str = "whatsapp_organico"
    evento_tipo: str | None = None
    evento_data: str | None = None
    peca_interesse: str | None = None
    tamanho: str | None = None
    cor: str | None = None
    valor_estimado: float | None = None
    followup_tentativas: int = 0
    motivo_descarte: str | None = None
    reaberto_de_lead_id: str | None = None
    status_alterado_em: datetime = Field(default_factory=datetime.now)
    status_alterado_por: str = "sistema"
    ultimo_contato_em: datetime = Field(default_factory=datetime.now)
    criado_em: datetime = Field(default_factory=datetime.now)


class LeadEventoModel(BaseModel):
    id: int
    tenant_id: str
    lead_id: str
    tipo: str
    de: str | None = None
    para: str | None = None
    autor: str = "sistema"
    motivo: str | None = None
    detalhe: dict[str, Any] = Field(default_factory=dict)
    criado_em: datetime = Field(default_factory=datetime.now)


class LeadService:
    """
    Serviço em memória / repositório para o ciclo de vida do Lead e execução da
    matriz de decisão de `identificar_lead` (§9.4, §17.10, AC 9.1-9.4).
    """

    def __init__(self):
        self.contatos: dict[str, ContatoModel] = {}  # key: f"{tenant_id}:{telefone}"
        self.leads: list[LeadModel] = []
        self.eventos: list[LeadEventoModel] = []
        self.janela_retomada_dias = 7

    def identificar_lead(
        self,
        tenant_id: str,
        telefone: str,
        push_name: str,
        origem: str = "whatsapp_organico",
        simulated_now: datetime | None = None,
    ) -> tuple[str, str, TipoEntrada]:
        now = simulated_now or datetime.now()
        key = f"{tenant_id}:{telefone}"

        # 1. Upsert Contato
        if key not in self.contatos:
            contato = ContatoModel(
                id=f"cnt_{len(self.contatos) + 1}",
                tenant_id=tenant_id,
                telefone=telefone,
                nome=push_name,
                primeiro_contato_em=now,
                ultimo_contato_em=now,
            )
            self.contatos[key] = contato
        else:
            contato = self.contatos[key]
            contato.ultimo_contato_em = now
            if push_name:
                contato.nome = push_name

        # Reversão de opt-out caso estivesse ativo
        opt_out_revertido = False
        if contato.opt_out:
            contato.opt_out = False
            opt_out_revertido = True

        # 2. Busca o último lead do contato
        leads_do_contato = [l for l in self.leads if l.contato_id == contato.id]
        ultimo_lead = leads_do_contato[-1] if leads_do_contato else None

        # 3. Matriz de Decisão §9.4
        if ultimo_lead is None:
            entrada: TipoEntrada = "primeiro_contato"
        elif opt_out_revertido or ultimo_lead.status in ("ganho", "descartado"):
            entrada = "reengajamento"
        elif (now - ultimo_lead.ultimo_contato_em) >= timedelta(days=self.janela_retomada_dias):
            entrada = "retomada"
        else:
            entrada = "continuacao"

        # 4. Processa criação ou atualização
        if entrada in ("primeiro_contato", "reengajamento"):
            seq = (ultimo_lead.lead_seq + 1) if ultimo_lead else 1
            novo_lead = LeadModel(
                id=f"lead_{len(self.leads) + 1}",
                tenant_id=tenant_id,
                contato_id=contato.id,
                lead_seq=seq,
                status="novo",
                origem=origem,
                reaberto_de_lead_id=ultimo_lead.id if entrada == "reengajamento" else None,
                ultimo_contato_em=now,
                criado_em=now,
            )
            self.leads.append(novo_lead)
            contato.total_leads += 1

            self.eventos.append(
                LeadEventoModel(
                    id=len(self.eventos) + 1,
                    tenant_id=tenant_id,
                    lead_id=novo_lead.id,
                    tipo="lead_criado",
                    detalhe={"entrada": entrada, "opt_out_revertido": opt_out_revertido},
                )
            )
            lead_retornado_id = novo_lead.id
        else:
            ultimo_lead.ultimo_contato_em = now
            if entrada == "retomada":
                self.eventos.append(
                    LeadEventoModel(
                        id=len(self.eventos) + 1,
                        tenant_id=tenant_id,
                        lead_id=ultimo_lead.id,
                        tipo="reaberto",
                        detalhe={"dias_silencio": (now - ultimo_lead.ultimo_contato_em).days},
                    )
                )
            lead_retornado_id = ultimo_lead.id

        return contato.id, lead_retornado_id, entrada


# Singleton do lead service
lead_service = LeadService()
