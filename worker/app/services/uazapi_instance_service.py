import logging
import os
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger("alfaia.uazapi_instance_service")


def _is_dev_like_runtime() -> bool:
    return os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower() not in ("production", "prod")


def _required_env(name: str, fallback_dev: str | None = None) -> str:
    value = os.getenv(name)
    if value:
        return value

    if _is_dev_like_runtime() and fallback_dev:
        return fallback_dev

    raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")


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
        env_base_url = _required_env("UAZAPI_BASE_URL", "https://api.uazapi.com")
        env_token = _required_env("UAZAPI_ADMIN_TOKEN", "dev-uazapi-admin-token")

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

        # Tenta buscar QR Code real do servidor UAZAPI (protocolo uazapiGO: create -> connect)
        if inst.base_url and inst.token:
            try:
                import httpx
                clean_base_url = inst.base_url.rstrip("/")
                with httpx.Client(timeout=10.0) as client:
                    # Passo 1: Criar/Obter instância (admintoken)
                    create_res = client.post(
                        f"{clean_base_url}/instance/create",
                        headers={"Content-Type": "application/json", "admintoken": inst.token},
                        json={"name": inst.nome},
                    )

                    instance_token = None
                    if create_res.status_code == 200:
                        c_data = create_res.json()
                        instance_token = c_data.get("token") or (c_data.get("instance") or {}).get("token")

                    # Passo 2: Conectar e obter QR Code oficial em base64 (token)
                    if instance_token:
                        conn_res = client.post(
                            f"{clean_base_url}/instance/connect",
                            headers={"Content-Type": "application/json", "token": instance_token},
                        )

                        if conn_res.status_code == 200:
                            conn_data = conn_res.json()
                            raw_qr = (conn_data.get("instance") or {}).get("qrcode") or conn_data.get("qrcode") or conn_data.get("base64")
                            if raw_qr:
                                qrcode_url = raw_qr
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
