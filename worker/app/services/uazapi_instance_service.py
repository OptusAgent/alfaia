import logging
import os
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger("alfaia.uazapi_instance_service")


class UazapiInstanceModel:

    def __init__(
        self,
        id: str,
        tenant_id: str,
        nome: str,
        base_url: str,
        token: str,
        status: str = "desconectado",
        qrcode: str | None = None,
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.nome = nome
        self.base_url = base_url
        self.token = token
        self.status = status  # 'conectado', 'desconectado', 'gerando_qrcode'
        self.qrcode = qrcode
        self.criado_em = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "nome": self.nome,
            "base_url": self.base_url,
            "token": self.token[:4] + "****" if self.token and len(self.token) > 4 else "****",
            "status": self.status,
            "qrcode": self.qrcode,
            "criado_em": self.criado_em.isoformat(),
        }


class UazapiInstanceService:
    """
    Gerenciamento de Instâncias e Credenciais Reais da UAZAPI (CRUD).
    """

    def __init__(self):
        # Instância inicial real / configurável por env
        env_base_url = os.getenv("UAZAPI_BASE_URL", "https://api.uazapi.com")
        env_token = os.getenv("UAZAPI_ADMIN_TOKEN", "uazapi_admin_key_prod")

        self.instancias: list[UazapiInstanceModel] = [
            UazapiInstanceModel(
                id="inst_piloto",
                tenant_id="tenant_piloto",
                nome="Instância Piloto WhatsApp (UAZAPI)",
                base_url=env_base_url,
                token=env_token,
                status="conectado",
            )
        ]

    def listar_instancias(self, tenant_id: str = "tenant_piloto") -> list[dict[str, Any]]:
        return [inst.to_dict() for inst in self.instancias if inst.tenant_id == tenant_id]

    def criar_instancia(self, tenant_id: str, nome: str, base_url: str, token: str) -> dict[str, Any]:
        inst_id = f"inst_{str(uuid.uuid4())[:8]}"
        nova = UazapiInstanceModel(
            id=inst_id,
            tenant_id=tenant_id,
            nome=nome,
            base_url=base_url,
            token=token,
            status="desconectado",
        )
        self.instancias.append(nova)
        logger.info(f"Instância UAZAPI criada [id={inst_id}, nome='{nome}']")
        return {"sucesso": True, "instancia": nova.to_dict()}

    def atualizar_instancia(
        self, tenant_id: str, inst_id: str, nome: str, base_url: str, token: str, status: str | None = None
    ) -> dict[str, Any]:
        inst = next((i for i in self.instancias if i.id == inst_id and i.tenant_id == tenant_id), None)
        if not inst:
            return {"sucesso": False, "status_code": 404, "erro": "Instância não encontrada"}

        inst.nome = nome
        inst.base_url = base_url
        if token and not token.endswith("****"):
            inst.token = token
        if status:
            inst.status = status

        logger.info(f"Instância UAZAPI atualizada [id={inst_id}]")
        return {"sucesso": True, "instancia": inst.to_dict()}

    def deletar_instancia(self, tenant_id: str, inst_id: str) -> dict[str, Any]:
        self.instancias = [i for i in self.instancias if not (i.id == inst_id and i.tenant_id == tenant_id)]
        logger.info(f"Instância UAZAPI removida [id={inst_id}]")
        return {"sucesso": True, "inst_id": inst_id}

    def gerar_qrcode(self, tenant_id: str, inst_id: str) -> dict[str, Any]:
        inst = next((i for i in self.instancias if i.id == inst_id and i.tenant_id == tenant_id), None)
        if not inst:
            return {"sucesso": False, "status_code": 404, "erro": "Instância não encontrada"}

        # Simula geração de QR Code base64 para pareamento real no WhatsApp
        inst.status = "gerando_qrcode"
        inst.qrcode = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        return {
            "sucesso": True,
            "instancia_id": inst_id,
            "qrcode": inst.qrcode,
            "status": "gerando_qrcode",
            "mensagem": "Escaneie o QR Code no seu aplicativo do WhatsApp",
        }


uazapi_instance_service = UazapiInstanceService()
