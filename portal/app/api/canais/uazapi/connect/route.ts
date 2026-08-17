import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

type UazapiInstance = {
  id?: string;
  name?: string;
  status?: string;
  token?: string;
  qrcode?: string;
  instance?: {
    id?: string;
    token?: string;
    qrcode?: string;
  };
  base64?: string;
};

function normalizarStatusUazapi(status?: string | null) {
  const normalized = String(status || "").toLowerCase();
  if (["connected", "conectado", "open", "online"].includes(normalized)) {
    return "conectado";
  }
  if (["connecting", "qrcode", "qr", "pairing"].includes(normalized)) {
    return "conectando";
  }
  if (["disconnected", "desconectado", "close", "closed", "offline"].includes(normalized)) {
    return "desconectado";
  }
  return normalized || "desconhecido";
}

function isDevLikeRuntime() {
  return process.env.NODE_ENV !== "production";
}

function getRequiredEnv(name: string, fallbackDev?: string) {
  const value = process.env[name];
  if (value) return value;

  if (isDevLikeRuntime() && fallbackDev) {
    return fallbackDev;
  }

  throw new Error(`Variavel de ambiente obrigatoria ausente: ${name}`);
}

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

    const uazapiAdminToken = getRequiredEnv("UAZAPI_ADMIN_TOKEN", "dev-uazapi-admin-token");

    const workerUrl = (
      process.env.WORKER_URL || getRequiredEnv("NEXT_PUBLIC_WORKER_URL", "http://localhost:8000")
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
        const createData = (await createRes.json()) as UazapiInstance;
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
        const webhookBody = {
          url: webhookUrl,
          enabled: true,
          addUrlEvents: false,
          addUrlTypesMessages: false,
          events: ["messages"],
          excludeMessages: ["wasSentByApi", "isGroupYes"],
          excludeEvents: ["wasSentByApi", "isGroupYes"],
        };

        const webhookRes = await fetch(`${uazapiBaseUrl}/webhook/${encodeURIComponent(nome)}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            token: instanceToken,
          },
          body: JSON.stringify(webhookBody),
        });

        if (webhookRes.ok) {
          webhookCreated = true;
        } else {
          const fallbackWebhookRes = await fetch(`${uazapiBaseUrl}/webhook`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              token: instanceToken,
            },
            body: JSON.stringify(webhookBody),
          });
          webhookCreated = fallbackWebhookRes.ok;
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
          const connectData = (await connectRes.json()) as UazapiInstance;
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

    if (!instanceToken && !isDevLikeRuntime()) {
      return NextResponse.json(
        {
          error: errorMessage || "UAZAPI nao retornou token da instancia.",
        },
        { status: 502 }
      );
    }

    // 4. Salvar canal real no banco de dados Supabase (tabela canais)
    try {
      const supabase = await createClient();
      const { data: tenantData } = await supabase.from("tenants").select("id").limit(1).single();
      const tenantId = tenantData?.id;

      if (!tenantId) {
        return NextResponse.json({ error: "Nenhum tenant ativo encontrado para registrar o canal." }, { status: 400 });
      }

      const now = new Date().toISOString();
      const payload = {
        tenant_id: tenantId,
        provider: "uazapi",
        nome: nome,
        telefone: telefone?.replace(/\D/g, "") || null,
        ativo: true,
        uazapi_base_url: uazapiBaseUrl,
        uazapi_instancia: nome,
        uazapi_token: instanceToken,
        status: isLiveFromUazapi ? "conectando" : "desconectado",
        qualidade: "BOA",
        ultimo_healthcheck_em: now,
        ultimo_status_raw: {
          instanceId,
          webhookCreated,
          isLiveFromUazapi,
          errorMessage: errorMessage || null,
        },
        editado_em: now,
      };

      const { data: existente } = await supabase
        .from("canais")
        .select("id")
        .eq("tenant_id", tenantId)
        .eq("uazapi_instancia", nome)
        .is("excluido_em", null)
        .maybeSingle();

      await supabase.from("canais").update({ ativo: false, editado_em: now }).eq("tenant_id", tenantId).neq("uazapi_instancia", nome);

      const result = existente?.id
        ? await supabase.from("canais").update(payload).eq("id", existente.id)
        : await supabase.from("canais").insert(payload);

      if (result.error) {
        throw result.error;
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Erro ao salvar canal no Supabase";
      return NextResponse.json({ error: msg }, { status: 500 });
    }

    // Fallback de exibição em ambiente sem UAZAPI remota
    if (!qrcodeUrl && isDevLikeRuntime()) {
      const cleanPhone = (telefone || "5585988112233").replace(/\D/g, "");
      const pairingPayload = `2@AlfaiaWorker_${nome}_${cleanPhone},${Date.now()}`;
      qrcodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=350x350&data=${encodeURIComponent(pairingPayload)}`;
    }

    if (!qrcodeUrl) {
      return NextResponse.json(
        { error: errorMessage || "UAZAPI nao retornou QR Code da instancia." },
        { status: 502 }
      );
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

  const uazapiAdminToken = getRequiredEnv("UAZAPI_ADMIN_TOKEN", "dev-uazapi-admin-token");

  try {
    const res = await fetch(`${uazapiBaseUrl}/instance/fetchInstances`, {
      headers: { admintoken: uazapiAdminToken },
      cache: "no-store",
    });
    if (res.ok) {
      const data = (await res.json()) as UazapiInstance[];
      const match = (data || []).find((i) => i.name === instancia || i.id === instancia);
      if (match) {
        const status = normalizarStatusUazapi(match.status);
        const supabase = await createClient();
        await supabase
          .from("canais")
          .update({
            status,
            qualidade: status === "conectado" ? "EXCELENTE" : "BOA",
            ultimo_healthcheck_em: new Date().toISOString(),
            ultimo_status_raw: match,
            editado_em: new Date().toISOString(),
          })
          .eq("uazapi_instancia", instancia)
          .is("excluido_em", null);

        return NextResponse.json({ status });
      }
    }
  } catch {
    // fallback
  }

  return NextResponse.json({ status: "conectando" });
}
