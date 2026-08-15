import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { nome, telefone } = await req.json();

    if (!nome) {
      return NextResponse.json({ error: "Nome da instância é obrigatório" }, { status: 400 });
    }

    const workerUrl = (
      process.env.WORKER_URL ||
      process.env.NEXT_PUBLIC_WORKER_URL ||
      "http://localhost:8000"
    ).replace(/\/$/, "");

    let qrcodeUrl = "";
    let status = "qrcode";
    let workerConnected = false;
    let errorMessage = "";

    // 1. Chama o serviço de backend alfaia-worker (na VPS / Cloud Run) para criar a instância
    try {
      const createRes = await fetch(`${workerUrl}/instancias`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_id: "tenant_piloto",
          nome: nome,
          base_url: process.env.UAZAPI_BASE_URL || "https://api.uazapi.com",
          token: process.env.UAZAPI_ADMIN_TOKEN || "fake_token",
        }),
      });

      if (createRes.ok) {
        const createData = await createRes.json();
        const instId = createData.instancia?.id;

        if (instId) {
          // 2. Chama o worker para gerar o QR Code oficial da instância UAZAPI
          const qrRes = await fetch(`${workerUrl}/instancias/${instId}/qrcode?tenant_id=tenant_piloto`, {
            method: "POST",
          });

          if (qrRes.ok) {
            const qrData = await qrRes.json();
            qrcodeUrl = qrData.qrcode;
            status = qrData.status || "qrcode";
            workerConnected = true;
          }
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro de conexão";
      errorMessage = `Worker (${workerUrl}) inacessível: ${msg}`;
    }

    // 3. Fallback / Dev Mode: Se o worker estiver offline ou não retornar QR Code
    if (!qrcodeUrl) {
      const cleanPhone = (telefone || "5585988112233").replace(/\D/g, "");
      const pairingPayload = `2@AlfaiaWorker_${nome}_${cleanPhone},${Date.now()}`;
      qrcodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=350x350&data=${encodeURIComponent(pairingPayload)}`;
    }

    return NextResponse.json({
      success: true,
      instancia: nome,
      telefone: telefone || null,
      status,
      qrcode: qrcodeUrl,
      workerConnected,
      workerUrl,
      error: errorMessage || null,
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Erro desconhecido";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const instancia = searchParams.get("instancia");

  const workerUrl = (
    process.env.WORKER_URL ||
    process.env.NEXT_PUBLIC_WORKER_URL ||
    "http://localhost:8000"
  ).replace(/\/$/, "");

  try {
    const res = await fetch(`${workerUrl}/instancias?tenant_id=tenant_piloto`);
    if (res.ok) {
      const data = await res.json();
      const inst = (data.instancias || []).find((i: { nome: string }) => i.nome === instancia);
      if (inst) {
        return NextResponse.json({ status: inst.status });
      }
    }
  } catch {
    // fallback
  }

  return NextResponse.json({ status: "conectando" });
}
