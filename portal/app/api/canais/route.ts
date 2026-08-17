import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  try {
    const supabase = await createClient();
    const { data: dbCanais } = await supabase.from("canais").select("*");

    const uazapiBaseUrl = (
      process.env.UAZAPI_BASE_URL ||
      process.env.NEXT_PUBLIC_UAZAPI_BASE_URL ||
      "https://optus.uazapi.com"
    ).replace(/\/$/, "");

    const uazapiAdminToken =
      process.env.UAZAPI_ADMIN_TOKEN ||
      "0TzblrcqZ04deiwH2kgLapvZuaI6fRws4sBba2E1Nwlw3rK2j4";

    let realUazapiInstances: { id?: string; name?: string; status?: string; token?: string; created?: string }[] = [];
    try {
      const uazapiRes = await fetch(`${uazapiBaseUrl}/instance/fetchInstances`, {
        headers: { admintoken: uazapiAdminToken },
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
      const canaisComStatusReal = dbCanais.map((c) => {
        if (c.provider === "uazapi" || c.provider === "UAZAPI") {
          const match = realUazapiInstances.find((i) => i.name === c.uazapi_instancia || i.id === c.uazapi_instancia);
          if (match) {
            return {
              ...c,
              status: match.status === "connected" ? "conectado" : match.status || c.status,
              qualidade: match.status === "connected" ? "EXCELENTE" : c.qualidade,
            };
          }
        }
        return c;
      });
      return NextResponse.json({ canais: canaisComStatusReal });
    }

    // Se ainda não houver canais no banco, mapeia as instâncias reais retornadas diretamente da UAZAPI
    if (realUazapiInstances.length > 0) {
      const canaisReais = realUazapiInstances.map((inst, idx) => ({
        id: inst.id || `uazapi-${idx}`,
        tenant_id: "piloto-01",
        provider: "UAZAPI",
        nome: `WhatsApp Instância: ${inst.name || inst.id}`,
        ativo: idx === 0,
        status: inst.status === "connected" ? "conectado" : inst.status || "desconectado",
        qualidade: inst.status === "connected" ? "EXCELENTE" : "BOA",
        uazapi_instancia: inst.name || inst.id,
        uazapi_token: inst.token || "****",
        criado_em: inst.created || new Date().toISOString(),
      }));
      return NextResponse.json({ canais: canaisReais });
    }

    return NextResponse.json({ canais: [] });
  } catch {
    return NextResponse.json({ canais: [] });
  }
}

export async function POST(req: Request) {
  try {
    const { canalId, ativar } = await req.json();
    const supabase = await createClient();

    if (ativar) {
      await supabase.from("canais").update({ ativo: false }).neq("id", canalId);
      await supabase.from("canais").update({ ativo: true }).eq("id", canalId);
    } else {
      await supabase.from("canais").update({ ativo: false }).eq("id", canalId);
    }

    const { data: canaisAtualizados } = await supabase.from("canais").select("*");
    return NextResponse.json({ ok: true, canais: canaisAtualizados || [] });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Erro desconhecido";
    return NextResponse.json({ error: msg }, { status: 400 });
  }
}
