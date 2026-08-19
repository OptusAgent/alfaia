"""
wl-fake-api — serviço HTTP standalone que simula a API real da WebLocação,
sob o contrato de PRD §7.2, para exercitar `WL_MODO=real` do worker ALFAIA
ponta a ponta (cliente HTTP real, timeout, retry 5xx, tradução da camada
anticorrupção) sem depender do contrato real (ainda não fechado — Q1-Q3
do PRD).

Não confundir com `WLMockAdapter` (worker/app/services/weblocacao_service.py),
que é o modo in-process `WL_MODO=mock` usado no dia a dia de desenvolvimento.
Este serviço é um segundo mock, deliberado: um ERP fake real, atrás de rede,
para testar o caminho real-mode.

Auth: aceita qualquer `Authorization: Bearer <token>` não vazio, simulando
autenticação por chave por tenant (I1) sem impor um valor específico.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.store import store

app = FastAPI(
    title="wl-fake-api",
    description="ERP fake da WebLocação para testar WL_MODO=real. Dado sintético — ver README.",
    version="0.1.0",
)

# Serve as imagens do catálogo sintético localmente (docs/img/) enquanto o
# upload para o Supabase Storage não é executado — ver README, seção Limitações.
_IMG_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "img"
if _IMG_DIR.is_dir():
    app.mount("/static/catalogo", StaticFiles(directory=str(_IMG_DIR)), name="catalogo")


class AgendaCreateBody(BaseModel):
    tipo: str = "prova"
    data: str
    hora: str
    cliente_nome: str
    cliente_telefone: str | None = None
    produto_id: str | None = None
    observacao: str | None = None


def _exigir_auth(authorization: str | None) -> None:
    if not authorization or not authorization.lower().startswith("bearer ") or len(authorization) < 12:
        raise HTTPException(status_code=401, detail="Credencial ausente ou inválida.")


@app.get("/health")
def health():
    return {"status": "ok", "servico": "wl-fake-api"}


@app.get("/produtos")
def listar_produtos(
    authorization: str | None = Header(default=None),
    data_inicio: str | None = Query(default=None),
    data_fim: str | None = Query(default=None),
    categoria: str | None = Query(default=None),
    tamanho: str | None = Query(default=None),
    cor: str | None = Query(default=None),
    estilo: str | None = Query(default=None),
    q: str | None = Query(default=None),
):
    _exigir_auth(authorization)
    return store.listar_produtos(categoria=categoria, tamanho=tamanho, cor=cor, estilo=estilo, q=q)


@app.get("/produtos/{produto_id}")
def obter_produto(produto_id: str, authorization: str | None = Header(default=None)):
    _exigir_auth(authorization)
    produto = store.obter_produto(produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


@app.get("/agenda/slots")
def listar_slots(
    authorization: str | None = Header(default=None),
    tipo: str = Query(default="prova"),
    data_inicio: str = Query(...),
    data_fim: str | None = Query(default=None),
):
    _exigir_auth(authorization)
    return store.listar_slots(tipo=tipo, data_inicio=data_inicio, data_fim=data_fim)


@app.post("/agenda")
def criar_agendamento(
    body: AgendaCreateBody,
    authorization: str | None = Header(default=None),
):
    _exigir_auth(authorization)
    try:
        registro = store.criar_agendamento(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": registro["id"], "status": registro["status"]}


@app.get("/agenda")
def listar_agendamentos(
    authorization: str | None = Header(default=None),
    data_inicio: str = Query(...),
    data_fim: str | None = Query(default=None),
):
    _exigir_auth(authorization)
    return store.listar_agendamentos(data_inicio=data_inicio, data_fim=data_fim)
