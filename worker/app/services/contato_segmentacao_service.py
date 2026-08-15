import logging
from typing import Any

from app.services.lead_service import lead_service

logger = logging.getLogger("alfaia.contato_segmentacao")


class ContatoSegmentacaoService:
    """
    Engine de Segmentação da Base Permanente de Contatos (PRD §15.1, AC 1-4).
    - Repositório permanente de todo telefone que já interagiu (AC 1).
    - Filtros por tipo de evento, papel, status final do lead, faixa de valor e tags (AC 2).
    - Exibição de tags de leads descartados para remarketing (AC 3, AC 15.1).
    """

    def buscar_contatos_segmentados(
        self,
        tenant_id: str = "tenant_piloto",
        tipo_evento: str | None = None,
        papel: str | None = None,
        status_final_lead: str | None = None,
        tag: str | None = None,
        origem: str | None = None,
    ) -> list[dict[str, Any]]:
        resultados = []

        for key, contato in lead_service.contatos.items():
            if contato.tenant_id != tenant_id:
                continue

            # Busca leads associados a este contato
            leads_do_contato = [l for l in lead_service.leads if l.contato_id == contato.id and l.tenant_id == tenant_id]
            ultimo_lead = leads_do_contato[-1] if leads_do_contato else None

            # 1. Filtro por tipo_evento (ex: noiva, debutante, formatura)
            if tipo_evento:
                tags_contato = getattr(contato, "tags", [])
                if tipo_evento.lower() not in [t.lower() for t in tags_contato]:
                    # Checa também no interesse do último lead se houver
                    if not ultimo_lead or tipo_evento.lower() not in str(getattr(ultimo_lead, "interesse_resumo", "")).lower():
                        continue

            # 2. Filtro por papel (ex: noiva, mae_da_noiva, madrinha)
            if papel:
                tags_contato = getattr(contato, "tags", [])
                if papel.lower() not in [t.lower() for t in tags_contato]:
                    continue

            # 3. Filtro por status_final_lead (ex: ganho, descartado, negociando)
            if status_final_lead:
                if not ultimo_lead or ultimo_lead.status.lower() != status_final_lead.lower():
                    continue

            # 4. Filtro por tag específica
            if tag:
                tags_contato = getattr(contato, "tags", [])
                if tag.lower() not in [t.lower() for t in tags_contato]:
                    continue

            # Constrói o DTO enriquecido para exibição
            tags_finais = list(getattr(contato, "tags", []))
            if ultimo_lead and ultimo_lead.status == "descartado" and "descartado" not in tags_finais:
                tags_finais.append("descartado")

            dto = {
                "id": contato.id,
                "tenant_id": contato.tenant_id,
                "telefone": contato.telefone,
                "nome": contato.nome,
                "opt_out": contato.opt_out,
                "tags": tags_finais,
                "ultimo_lead_id": ultimo_lead.id if ultimo_lead else None,
                "ultimo_lead_status": ultimo_lead.status if ultimo_lead else "sem_lead",
                "motivo_descarte": ultimo_lead.motivo_descarte if ultimo_lead and ultimo_lead.status == "descartado" else None,
                "criado_em": getattr(contato, "criado_em", None),
            }
            resultados.append(dto)

        logger.info(f"Segmentação executada com sucesso [total_encontrados={len(resultados)}]")
        return resultados

    def obter_todas_tags(self, tenant_id: str = "tenant_piloto") -> list[str]:
        tags_unicas = set()
        for key, contato in lead_service.contatos.items():
            if contato.tenant_id == tenant_id:
                for t in getattr(contato, "tags", []):
                    tags_unicas.add(t)
        return sorted(list(tags_unicas))


contato_segmentacao_service = ContatoSegmentacaoService()
