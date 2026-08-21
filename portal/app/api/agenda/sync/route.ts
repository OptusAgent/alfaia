import { NextResponse } from "next/server";

function getRequiredEnv(name: string) {
  const value = process.env[name];
  if (value) return value;

  throw new Error(`Variavel de ambiente obrigatoria ausente: ${name}`);
}

export async function POST(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const tenantId = searchParams.get("tenant_id");
    const inicio = searchParams.get("inicio");
    const fim = searchParams.get("fim");

    if (!tenantId) {
      return NextResponse.json({ error: "tenant_id é obrigatório" }, { status: 400 });
    }

    const workerUrl = (
      process.env.WORKER_URL || getRequiredEnv("NEXT_PUBLIC_WORKER_URL")
    ).replace(/\/$/, "");

    const params = new URLSearchParams({ tenant_id: tenantId });
    if (inicio) params.set("inicio", inicio);
    if (fim) params.set("fim", fim);

    const res = await fetch(`${workerUrl}/api/agenda/sync?${params.toString()}`, {
      method: "POST",
    });

    if (!res.ok) {
      return NextResponse.json({ error: `Worker retornou HTTP ${res.status}` }, { status: 502 });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Erro desconhecido";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
