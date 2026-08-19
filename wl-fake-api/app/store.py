"""
Estado em memória da wl-fake-api, semeado a partir do catálogo sintético
(wl-fake-api/data/catalogo_sintetico.json).

Este módulo simula o "banco do ERP" do lado da WebLocação fake: cada peça do
catálogo é explodida em uma linha por tamanho (SKU), porque o contrato de
GET /produtos (PRD §7.2) retorna um `tamanho` singular por item, não uma
lista de tamanhos por peça.

DADO SINTÉTICO — ver wl-fake-api/README.md. Não é o catálogo real de nenhuma
locadora.
"""
from __future__ import annotations

import json
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

CATALOGO_PATH = Path(__file__).resolve().parent.parent / "data" / "catalogo_sintetico.json"

SLOT_HORARIOS = ["09:00", "11:00", "14:00", "16:00"]
SLOT_VAGAS_TOTAIS = 2


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acento.strip().lower()


def _carregar_catalogo() -> list[dict[str, Any]]:
    bruto = json.loads(CATALOGO_PATH.read_text(encoding="utf-8"))
    return bruto["produtos"]


class WLFakeStore:
    """Estado do ERP fake: catálogo explodido em SKUs, slots e agendamentos."""

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self._produtos_base = _carregar_catalogo()
        self._skus: list[dict[str, Any]] = []
        for produto in self._produtos_base:
            for variacao in produto["tamanhos"]:
                self._skus.append(
                    {
                        "id": f"{produto['id']}_{variacao['tamanho']}",
                        "codigo": produto["codigo"],
                        "nome": produto["nome"],
                        "categoria": produto["categoria"],
                        "tamanho": variacao["tamanho"],
                        "cor": produto["cor"],
                        "estilo": produto["estilo"],
                        "tecido": produto["tecido"],
                        "valor_locacao": produto["valor_locacao"],
                        "estoque": variacao["estoque"],
                        "foto_url": f"/static/catalogo/{produto['arquivo_origem']}",
                        "arquivo_origem": produto["arquivo_origem"],
                    }
                )
        self._agendamentos: dict[str, dict[str, Any]] = {}
        self._vagas_ocupadas: dict[tuple[str, str], int] = {}
        self._proximo_agendamento_id = 1

    @staticmethod
    def _status(sku: dict[str, Any]) -> str:
        return "disponivel" if sku["estoque"] > 0 else "indisponivel"

    def _sku_para_produto_response(self, sku: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": sku["id"],
            "codigo": sku["codigo"],
            "nome": sku["nome"],
            "categoria": sku["categoria"],
            "tamanho": sku["tamanho"],
            "cor": sku["cor"],
            "estilo": sku["estilo"],
            "valor_locacao": sku["valor_locacao"],
            "status": self._status(sku),
            "foto_url": sku["foto_url"],
        }

    def listar_produtos(
        self,
        categoria: str | None = None,
        tamanho: str | None = None,
        cor: str | None = None,
        estilo: str | None = None,
        q: str | None = None,
        **_ignorados: Any,
    ) -> list[dict[str, Any]]:
        resultado = self._skus

        if categoria:
            alvo = _normalizar(categoria)
            resultado = [s for s in resultado if alvo in _normalizar(s["categoria"])]
        if tamanho:
            resultado = [s for s in resultado if s["tamanho"] == tamanho]
        if cor:
            alvo = _normalizar(cor)
            resultado = [s for s in resultado if alvo in _normalizar(s["cor"])]
        if estilo:
            alvo = _normalizar(estilo)
            resultado = [s for s in resultado if alvo in _normalizar(s["estilo"])]
        if q:
            alvo = _normalizar(q)
            resultado = [
                s
                for s in resultado
                if alvo in _normalizar(s["nome"]) or alvo in _normalizar(s["categoria"])
            ]

        return [self._sku_para_produto_response(s) for s in resultado]

    def obter_produto(self, produto_id: str) -> dict[str, Any] | None:
        sku = next((s for s in self._skus if s["id"] == produto_id), None)
        if sku is None:
            return None

        resposta = self._sku_para_produto_response(sku)
        if resposta["status"] == "disponivel":
            hoje = date.today()
            resposta["disponivel_em"] = [
                {
                    "inicio": (hoje + timedelta(days=7)).isoformat(),
                    "fim": (hoje + timedelta(days=14)).isoformat(),
                },
                {
                    "inicio": (hoje + timedelta(days=30)).isoformat(),
                    "fim": (hoje + timedelta(days=37)).isoformat(),
                },
            ]
        else:
            resposta["disponivel_em"] = []
        return resposta

    def _vagas_livres(self, data_str: str, hora: str) -> int:
        ocupadas = self._vagas_ocupadas.get((data_str, hora), 0)
        return max(SLOT_VAGAS_TOTAIS - ocupadas, 0)

    def listar_slots(self, tipo: str, data_inicio: str, data_fim: str | None = None) -> list[dict[str, Any]]:
        inicio = datetime.fromisoformat(data_inicio).date()
        fim = datetime.fromisoformat(data_fim).date() if data_fim else inicio

        slots = []
        dia = inicio
        while dia <= fim:
            for hora in SLOT_HORARIOS:
                data_str = dia.isoformat()
                slots.append(
                    {
                        "data": data_str,
                        "hora": hora,
                        "vagas_totais": SLOT_VAGAS_TOTAIS,
                        "vagas_livres": self._vagas_livres(data_str, hora),
                    }
                )
            dia += timedelta(days=1)
        return slots

    def criar_agendamento(self, dados: dict[str, Any]) -> dict[str, Any]:
        data_str = dados["data"]
        hora = dados["hora"]

        if self._vagas_livres(data_str, hora) <= 0:
            raise ValueError(f"Sem vagas livres para {data_str} {hora}")

        chave = (data_str, hora)
        self._vagas_ocupadas[chave] = self._vagas_ocupadas.get(chave, 0) + 1

        agendamento_id = f"wl_ag_{self._proximo_agendamento_id}"
        self._proximo_agendamento_id += 1

        registro = {
            "id": agendamento_id,
            "status": "confirmado",
            "tipo": dados.get("tipo", "prova"),
            "data": data_str,
            "hora": hora,
            "cliente_nome": dados["cliente_nome"],
            "cliente_telefone": dados.get("cliente_telefone", ""),
            "produto": dados.get("produto_id"),
            "origem": dados.get("origem", "automacao"),
            "observacao": dados.get("observacao"),
        }
        self._agendamentos[agendamento_id] = registro
        return dict(registro)

    def listar_agendamentos(self, data_inicio: str, data_fim: str | None = None) -> list[dict[str, Any]]:
        inicio = datetime.fromisoformat(data_inicio).date()
        fim = datetime.fromisoformat(data_fim).date() if data_fim else inicio
        return [
            dict(ag)
            for ag in self._agendamentos.values()
            if inicio <= datetime.fromisoformat(ag["data"]).date() <= fim
        ]


store = WLFakeStore()
