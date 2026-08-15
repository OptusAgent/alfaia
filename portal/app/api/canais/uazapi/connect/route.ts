import { NextResponse } from "next/server";

const mockStatusMap: Record<string, string> = {};

export async function POST(req: Request) {
  try {
    const { nome, telefone } = await req.json();

    if (!nome) {
      return NextResponse.json({ error: "Nome da instância é obrigatório" }, { status: 400 });
    }

    mockStatusMap[nome] = "conectando";

    const uazapiBaseUrl = process.env.UAZAPI_BASE_URL || process.env.NEXT_PUBLIC_UAZAPI_BASE_URL;
    const uazapiAdminToken = process.env.UAZAPI_ADMIN_TOKEN;

    let qrcodeUrl = "";
    let isLiveFromUazapi = false;
    let errorMessage = "";

    // 1. Tenta integração com o servidor UAZAPI real se a URL estiver configurada
    if (uazapiBaseUrl && uazapiAdminToken) {
      try {
        const cleanBaseUrl = uazapiBaseUrl.replace(/\/$/, "");
        const uazapiRes = await fetch(`${cleanBaseUrl}/instance/connect/${encodeURIComponent(nome)}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            token: uazapiAdminToken,
            apikey: uazapiAdminToken,
          },
          body: JSON.stringify({ name: nome, phone: telefone }),
        });

        if (uazapiRes.ok) {
          const uazapiData = await uazapiRes.json();
          const rawQr = uazapiData.qrcode || uazapiData.base64 || uazapiData.code;

          if (rawQr) {
            isLiveFromUazapi = true;
            if (rawQr.startsWith("data:image")) {
              qrcodeUrl = rawQr;
            } else {
              // Se o UAZAPI retornar a string de pareamento (ex: 2@...), converte para QR Code escaneável
              qrcodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=350x350&data=${encodeURIComponent(rawQr)}`;
            }
          }
        } else {
          errorMessage = `UAZAPI HTTP ${uazapiRes.status}`;
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Falha na conexão UAZAPI";
        errorMessage = `Servidor UAZAPI inacessível: ${msg}`;
      }
    }

    // 2. Se não houver servidor UAZAPI ativo configurado
    if (!qrcodeUrl) {
      const cleanPhone = (telefone || "5585988112233").replace(/\D/g, "");
      // Mock pairing code no formato 2@... para exibição
      const mockPairingString = `2@AlfaiaWebSession_${nome}_${cleanPhone},${Date.now()}`;
      qrcodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=350x350&data=${encodeURIComponent(mockPairingString)}`;
    }

    return NextResponse.json({
      success: true,
      instancia: nome,
      telefone: telefone || null,
      status: "qrcode",
      qrcode: qrcodeUrl,
      isLive: isLiveFromUazapi,
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

  if (!instancia) {
    return NextResponse.json({ status: "desconectado" });
  }

  const currentStatus = mockStatusMap[instancia] || "conectando";
  return NextResponse.json({ status: currentStatus });
}
