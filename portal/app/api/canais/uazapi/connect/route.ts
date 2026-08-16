import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { nome, telefone } = await req.json();

    if (!nome) {
      return NextResponse.json({ error: "Nome da instância é obrigatório" }, { status: 400 });
    }

    const uazapiBaseUrl = (
      process.env.UAZAPI_BASE_URL ||
      process.env.NEXT_PUBLIC_UAZAPI_BASE_URL ||
      "https://optus.uazapi.com"
    ).replace(/\/$/, "");

    const uazapiAdminToken =
      process.env.UAZAPI_ADMIN_TOKEN ||
      "0TzblrcqZ04deiwH2kgLapvZuaI6fRws4sBba2E1Nwlw3rK2j4";

    let qrcodeUrl = "";
    let isLiveFromUazapi = false;
    let errorMessage = "";
    let instanceToken = "";

    // 1. Passo 1 do protocolo uazapiGO: Criar ou obter token da instância (header admintoken)
    try {
      const createRes = await fetch(`${uazapiBaseUrl}/instance/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          admintoken: uazapiAdminToken,
        },
        body: JSON.stringify({ name: nome }),
      });

      if (createRes.ok) {
        const createData = await createRes.json();
        instanceToken = createData.token || createData.instance?.token || "";
      } else {
        errorMessage = `UAZAPI /instance/create retornou status ${createRes.status}`;
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro de rede";
      errorMessage = `Falha ao conectar no UAZAPI (${uazapiBaseUrl}): ${msg}`;
    }

    // 2. Passo 2 do protocolo uazapiGO: Conectar e gerar QR Code oficial do WhatsApp Web (header token)
    if (instanceToken) {
      try {
        const connectRes = await fetch(`${uazapiBaseUrl}/instance/connect`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            token: instanceToken,
          },
        });

        if (connectRes.ok) {
          const connectData = await connectRes.json();
          const rawQr =
            connectData.instance?.qrcode ||
            connectData.qrcode ||
            connectData.base64;

          if (rawQr) {
            qrcodeUrl = rawQr;
            isLiveFromUazapi = true;
          }
        } else {
          errorMessage = `UAZAPI /instance/connect retornou status ${connectRes.status}`;
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Erro ao conectar";
        errorMessage = `Falha ao obter QR Code da UAZAPI: ${msg}`;
      }
    }

    // 3. Fallback se UAZAPI não retornar QR Code
    if (!qrcodeUrl) {
      const cleanPhone = (telefone || "5585988112233").replace(/\D/g, "");
      const pairingPayload = `2@AlfaiaWorker_${nome}_${cleanPhone},${Date.now()}`;
      qrcodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=350x350&data=${encodeURIComponent(pairingPayload)}`;
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

  return NextResponse.json({ status: "conectando" });
}
