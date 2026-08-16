import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

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

    const workerUrl = (
      process.env.WORKER_URL ||
      process.env.NEXT_PUBLIC_WORKER_URL ||
      "https://alfaia-worker-4ztt6gkx7a-rj.a.run.app"
    ).replace(/\/$/, "");

    let qrcodeUrl = "";
    let isLiveFromUazapi = false;
    let errorMessage = "";
    let instanceToken = "";
    let instanceId = "";
    let webhookCreated = false;

    // 1. Passo 1: Criar/Obter a Instância na UAZAPI (header admintoken)
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
        instanceId = createData.instance?.id || "";
      } else {
        errorMessage = `UAZAPI /instance/create HTTP ${createRes.status}`;
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro de conexão";
      errorMessage = `Falha ao conectar no UAZAPI (${uazapiBaseUrl}): ${msg}`;
    }

    // 2. Passo 2: Configurar o Webhook Oficial na UAZAPI com as regras exatas do PRD & UI
    if (instanceToken) {
      try {
        const webhookUrl = `${workerUrl}/webhook/uazapi/${instanceToken}`;
        const webhookRes = await fetch(`${uazapiBaseUrl}/webhook`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            token: instanceToken,
          },
          body: JSON.stringify({
            url: webhookUrl,
            enabled: true,
            addUrlEvents: false,
            addUrlTypesMessages: false,
            events: ["messages"],
            excludeMessages: ["wasSentByApi", "isGroupYes"],
            excludeEvents: ["wasSentByApi", "isGroupYes"],
          }),
        });

        if (webhookRes.ok) {
          webhookCreated = true;
        }
      } catch (err: unknown) {
        console.warn("Erro ao registrar webhook na UAZAPI:", err);
      }

      // 3. Passo 3: Conectar e obter o QR Code oficial em Base64 PNG do WhatsApp Web Engine
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
        }
      } catch (err: unknown) {
        console.warn("Erro ao obter QR Code:", err);
      }
    }

    // 4. Salvar canal real no banco de dados Supabase (tabela canais)
    try {
      const supabase = await createClient();
      const { data: tenantData } = await supabase.from("tenants").select("id").limit(1).single();
      const tenantId = tenantData?.id;

      if (tenantId) {
        await supabase.from("canais").upsert(
          {
            tenant_id: tenantId,
            provider: "uazapi",
            nome: nome,
            ativo: true,
            uazapi_base_url: uazapiBaseUrl,
            uazapi_instancia: nome,
            uazapi_token: instanceToken,
            status: isLiveFromUazapi ? "gerando_qrcode" : "desconectado",
            qualidade: "BOA",
          },
          { onConflict: "tenant_id" }
        );
      }
    } catch (e) {
      console.warn("Aviso ao salvar canal no Supabase:", e);
    }

    // Fallback de exibição em ambiente sem UAZAPI remota
    if (!qrcodeUrl) {
      const cleanPhone = (telefone || "5585988112233").replace(/\D/g, "");
      const pairingPayload = `2@AlfaiaWorker_${nome}_${cleanPhone},${Date.now()}`;
      qrcodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=350x350&data=${encodeURIComponent(pairingPayload)}`;
    }

    return NextResponse.json({
      success: true,
      instancia: nome,
      instanceId,
      instanceToken,
      telefone: telefone || null,
      status: "qrcode",
      qrcode: qrcodeUrl,
      isLive: isLiveFromUazapi,
      webhookCreated,
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

  const uazapiBaseUrl = (
    process.env.UAZAPI_BASE_URL ||
    process.env.NEXT_PUBLIC_UAZAPI_BASE_URL ||
    "https://optus.uazapi.com"
  ).replace(/\/$/, "");

  const uazapiAdminToken =
    process.env.UAZAPI_ADMIN_TOKEN ||
    "0TzblrcqZ04deiwH2kgLapvZuaI6fRws4sBba2E1Nwlw3rK2j4";

  try {
    const res = await fetch(`${uazapiBaseUrl}/instance/fetchInstances`, {
      headers: { admintoken: uazapiAdminToken },
    });
    if (res.ok) {
      const data = await res.json();
      const match = (data || []).find((i: { name?: string }) => i.name === instancia);
      if (match) {
        return NextResponse.json({ status: match.status || "conectando" });
      }
    }
  } catch {
    // fallback
  }

  return NextResponse.json({ status: "conectando" });
}
