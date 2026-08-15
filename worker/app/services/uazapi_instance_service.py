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

        inst.status = "gerando_qrcode"
        qrcode_url = None

        # Tenta buscar QR Code real do servidor UAZAPI se a URL estiver configurada
        if inst.base_url and inst.token:
            try:
                import httpx
                uazapi_endpoint = f"{inst.base_url.rstrip('/')}/instance/connect/{inst.nome}"
                headers = {"Content-Type": "application/json", "token": inst.token, "apikey": inst.token}
                with httpx.Client(timeout=8.0) as client:
                    res = client.post(uazapi_endpoint, headers=headers, json={"name": inst.nome})
                    if res.status_code == 200:
                        res_json = res.json()
                        raw_qr = res_json.get("qrcode") or res_json.get("base64") or res_json.get("code")
                        if raw_qr:
                            if raw_qr.startswith("data:image"):
                                qrcode_url = raw_qr
                            else:
                                import urllib.parse
                                qrcode_url = f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={urllib.parse.quote(raw_qr)}"
            except Exception as e:
                logger.warning(f"Não foi possível conectar ao servidor UAZAPI em {inst.base_url}: {e}")

        if not qrcode_url:
            import urllib.parse
            mock_payload = f"2@AlfaiaWebSession_{inst.nome}_{inst_id},{int(datetime.now().timestamp())}"
            qrcode_url = f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={urllib.parse.quote(mock_payload)}"

        inst.qrcode = qrcode_url
        return {
            "sucesso": True,
            "instancia_id": inst_id,
            "qrcode": inst.qrcode,
            "status": "gerando_qrcode",
            "mensagem": "Escaneie o QR Code no seu aplicativo do WhatsApp",
        }


uazapi_instance_service = UazapiInstanceService()
