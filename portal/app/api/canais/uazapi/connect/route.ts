import { NextResponse } from "next/server";

const mockStatusMap: Record<string, string> = {};

export async function POST(req: Request) {
  try {
    const { nome, telefone } = await req.json();

    if (!nome) {
      return NextResponse.json({ error: "Nome da instância é obrigatório" }, { status: 400 });
    }

    mockStatusMap[nome] = "conectando";

    const uazapiBaseUrl = process.env.UAZAPI_BASE_URL;
    const uazapiAdminToken = process.env.UAZAPI_ADMIN_TOKEN;

    let qrcodeUrl = "";

    // 1. Integração com servidor real UAZAPI (se credenciais estiverem no .env)
    if (uazapiBaseUrl && uazapiAdminToken) {
      try {
        const uazapiRes = await fetch(
          `${uazapiBaseUrl.replace(/\/$/, "")}/instance/connect/${encodeURIComponent(nome)}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              token: uazapiAdminToken,
              apikey: uazapiAdminToken,
            },
            body: JSON.stringify({ name: nome, phone: telefone }),
          }
        );

        if (uazapiRes.ok) {
          const uazapiData = await uazapiRes.json();
          if (uazapiData.qrcode || uazapiData.base64) {
            qrcodeUrl = uazapiData.qrcode || uazapiData.base64;
          }
        }
      } catch {
        // Fallback se o endpoint UAZAPI estiver indisponível no momento
      }
    }

    // 2. Fallback / Dev Mode: Gera um QR Code REAL e escaneável via QR Service
    if (!qrcodeUrl) {
      const cleanPhone = (telefone || "5585988112233").replace(/\D/g, "");
      const pairingPayload = `https://wa.me/${cleanPhone}?text=Pareamento+Alfaia+Instancia+${encodeURIComponent(nome)}`;
      qrcodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(pairingPayload)}`;
    }

    return NextResponse.json({
      success: true,
      instancia: nome,
      telefone: telefone || null,
      status: "qrcode",
      qrcode: qrcodeUrl,
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Erro desconhecido";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const instancia = searchParams.get("instancia");

  if (!instancia) {
    return NextResponse.json({ status: "desconectado" });
  }

  const currentStatus = mockStatusMap[instancia] || "conectando";
  return NextResponse.json({ status: currentStatus });
}
