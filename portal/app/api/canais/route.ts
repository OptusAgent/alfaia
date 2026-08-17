import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

type UazapiInstance = {
  id?: string;
  name?: string;
  status?: string;
  token?: string;
  created?: string;
};

type CanalRow = {
  id: string;
  tenant_id: string;
  provider: string;
  nome: string;
  ativo: boolean;
  telefone?: string | null;
  status?: string | null;
  qualidade?: string | null;
  uazapi_base_url?: string | null;
  uazapi_instancia?: string | null;
  uazapi_token?: string | null;
  criado_em?: string | null;
  ultimo_healthcheck_em?: string | null;
  ultimo_status_raw?: Record<string, unknown> | null;
  excluido_em?: string | null;
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

function getRequiredEnv(name: string, fallbackDev?: string) {
  const value = process.env[name];
  if (value) return value;

  if (process.env.NODE_ENV !== "production" && fallbackDev) {
    return fallbackDev;
  }

  throw new Error(`Variavel de ambiente obrigatoria ausente: ${name}`);
}

export async function GET() {
  try {
    const supabase = await createClient();
    const { data: dbCanais } = await supabase
      .from("canais")
      .select("*")
      .is("excluido_em", null)
      .order("criado_em", { ascending: false });

    const uazapiBaseUrl = (
      process.env.UAZAPI_BASE_URL ||
      process.env.NEXT_PUBLIC_UAZAPI_BASE_URL ||
      "https://optus.uazapi.com"
    ).replace(/\/$/, "");

    const uazapiAdminToken = getRequiredEnv("UAZAPI_ADMIN_TOKEN", "dev-uazapi-admin-token");

    let realUazapiInstances: UazapiInstance[] = [];
    try {
      const uazapiRes = await fetch(`${uazapiBaseUrl}/instance/fetchInstances`, {
        headers: { admintoken: uazapiAdminToken },
        cache: "no-store",
      });
      if (uazapiRes.ok) {
        const instances = await uazapiRes.json();
        if (Array.isArray(instances)) {
          realUazapiInstances = instances;
        }
      }
    } catch {
      // fallback
    }

    if (dbCanais && dbCanais.length > 0) {
      const now = new Date().toISOString();
      const canaisComStatusReal = await Promise.all((dbCanais as CanalRow[]).map(async (c) => {
        const provider = String(c.provider || "").toLowerCase();
        if (provider === "uazapi") {
          const match = realUazapiInstances.find((i) => i.name === c.uazapi_instancia || i.id === c.uazapi_instancia);
          const status = normalizarStatusUazapi(match?.status || c.status);
          const qualidade = status === "conectado" ? "EXCELENTE" : c.qualidade || "BOA";

          if (match) {
            await supabase
              .from("canais")
              .update({
                status,
                qualidade,
                ultimo_healthcheck_em: now,
                ultimo_status_raw: match,
                editado_em: now,
              })
              .eq("id", c.id);

            return {
              ...c,
              provider,
              status,
              qualidade,
              ultimo_healthcheck_em: now,
              ultimo_status_raw: match,
            };
          }

          return { ...c, provider, status, qualidade };
        }
        return c;
      }));
      return NextResponse.json({ canais: canaisComStatusReal });
    }

    // Se ainda não houver canais no banco, mapeia as instâncias reais retornadas diretamente da UAZAPI
    if (realUazapiInstances.length > 0) {
      const canaisReais = realUazapiInstances.map((inst, idx) => ({
        id: inst.id || `uazapi-${idx}`,
        tenant_id: "piloto-01",
        provider: "uazapi",
        nome: `WhatsApp Instância: ${inst.name || inst.id}`,
        ativo: idx === 0,
        telefone: null,
        status: normalizarStatusUazapi(inst.status),
        qualidade: normalizarStatusUazapi(inst.status) === "conectado" ? "EXCELENTE" : "BOA",
        uazapi_instancia: inst.name || inst.id,
        uazapi_token: inst.token || "****",
        criado_em: inst.created || new Date().toISOString(),
        ultimo_healthcheck_em: new Date().toISOString(),
      }));
      return NextResponse.json({ canais: canaisReais });
    }

    return NextResponse.json({ canais: [] });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Erro ao carregar canais";
    return NextResponse.json({ error: msg, canais: [] }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const { canalId, ativar } = await req.json();
    const supabase = await createClient();

    if (ativar) {
      await supabase.from("canais").update({ ativo: false }).neq("id", canalId);
      const { error } = await supabase.from("canais").update({ ativo: true, editado_em: new Date().toISOString() }).eq("id", canalId);
      if (error) throw error;
    } else {
      const { error } = await supabase.from("canais").update({ ativo: false, editado_em: new Date().toISOString() }).eq("id", canalId);
      if (error) throw error;
    }

    const { data: canaisAtualizados } = await supabase.from("canais").select("*").is("excluido_em", null);
    return NextResponse.json({ ok: true, canais: canaisAtualizados || [] });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Erro desconhecido";
    return NextResponse.json({ error: msg }, { status: 400 });
  }
}
