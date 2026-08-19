"""
Sobe as 9 imagens de wl-fake-api/data (o catálogo sintético de teste) para o
bucket `wl-mock-catalogo` no Supabase Storage, e imprime os UPDATEs para
apontar `wl_mock.produtos.foto_url` para a URL pública resultante.

DADO SINTÉTICO — este script existe para popular o ambiente de teste da
wl-fake-api, não para subir catálogo real de locadora.

NÃO é executado automaticamente pela story: requer confirmação explícita
porque cria um bucket e escreve no único projeto Supabase do produto
(não há Supabase de dev separado — ver .claude/rules/alfaia-stack-deploy.md).

Uso:
    export SUPABASE_URL=...
    export SUPABASE_SERVICE_KEY=...   # service_role, nunca a anon key
    python3 scripts/upload_catalogo_wl_mock.py [--bucket wl-mock-catalogo] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = REPO_ROOT / "docs" / "img"
CATALOGO_PATH = REPO_ROOT / "wl-fake-api" / "data" / "catalogo_sintetico.json"

CONTENT_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


def carregar_arquivos_origem() -> list[str]:
    catalogo = json.loads(CATALOGO_PATH.read_text(encoding="utf-8"))
    return [p["arquivo_origem"] for p in catalogo["produtos"]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default="wl-mock-catalogo")
    parser.add_argument("--dry-run", action="store_true", help="Lista o que seria feito, sem chamar o Supabase.")
    args = parser.parse_args()

    arquivos = carregar_arquivos_origem()
    faltando = [f for f in arquivos if not (IMG_DIR / f).exists()]
    if faltando:
        print(f"Arquivos ausentes em {IMG_DIR}: {faltando}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[dry-run] bucket destino: {args.bucket}")
        for arquivo in arquivos:
            print(f"[dry-run] subiria {IMG_DIR / arquivo} -> {args.bucket}/{arquivo}")
        return 0

    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    service_key = os.environ["SUPABASE_SERVICE_KEY"]
    headers = {"Authorization": f"Bearer {service_key}", "apikey": service_key}

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            f"{supabase_url}/storage/v1/bucket",
            headers=headers,
            json={"id": args.bucket, "name": args.bucket, "public": True},
        )
        if resp.status_code not in (200, 201) and "already exists" not in resp.text.lower():
            print(f"Falha ao criar bucket: {resp.status_code} {resp.text}", file=sys.stderr)
            return 1

        updates_sql = []
        for arquivo in arquivos:
            caminho = IMG_DIR / arquivo
            content_type = CONTENT_TYPES.get(caminho.suffix.lower(), "application/octet-stream")

            with open(caminho, "rb") as fh:
                resp = client.post(
                    f"{supabase_url}/storage/v1/object/{args.bucket}/{arquivo}",
                    headers={**headers, "Content-Type": content_type, "x-upsert": "true"},
                    content=fh.read(),
                )
            if resp.status_code not in (200, 201):
                print(f"Falha ao subir {arquivo}: {resp.status_code} {resp.text}", file=sys.stderr)
                continue

            url_publica = f"{supabase_url}/storage/v1/object/public/{args.bucket}/{arquivo}"
            print(f"OK  {arquivo} -> {url_publica}")
            updates_sql.append(
                f"update wl_mock.produtos set foto_url = '{url_publica}' where arquivo_origem = '{arquivo}';"
            )

    print("\n-- Rode manualmente no projeto Supabase para apontar o catálogo às URLs reais:")
    print("\n".join(updates_sql))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
