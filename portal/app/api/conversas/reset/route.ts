import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { getActiveTenant } from "@/lib/tenant";

function normalizarTelefone(raw?: string | null) {
  if (!raw) return "";
  let digits = String(raw).replace(/\D/g, "");
  if ((digits.length === 10 || digits.length === 11) && !digits.startsWith("55")) {
    digits = `55${digits}`;
  }
  return digits;
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const confirmacao = String(body.confirmacao || "");
    const telefone = normalizarTelefone(body.telefone);
    const motivo = String(body.motivo || "Reset manual para testes de memoria");

    if (confirmacao !== "RESETAR") {
      return NextResponse.json({ error: "Digite RESETAR para confirmar." }, { status: 400 });
    }

    const tenant = await getActiveTenant();
    if (!tenant) {
      return NextResponse.json({ error: "Tenant ativo nao encontrado." }, { status: 401 });
    }
    if (tenant.papel !== "dono") {
      return NextResponse.json({ error: "Apenas o dono pode resetar conversas." }, { status: 403 });
    }

    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    const contatoQuery = supabase
      .from("contatos")
      .select("id")
      .eq("tenant_id", tenant.tenant_id);
    if (telefone) contatoQuery.eq("telefone", telefone);

    const { data: contatos } = await contatoQuery;
    const contatoIds = (contatos || []).map((row) => row.id);

    const leadQuery = supabase
      .from("leads")
      .select("id")
      .eq("tenant_id", tenant.tenant_id);
    if (contatoIds.length > 0) leadQuery.in("contato_id", contatoIds);
    if (telefone && contatoIds.length === 0) {
      return NextResponse.json({
        ok: true,
        telefone,
        removidos: { mensagens: 0, conversas: 0, leads: 0, contatos: 0 },
        aviso: "Nenhuma memoria encontrada para este telefone.",
      });
    }

    const { data: leads } = await leadQuery;
    const leadIds = (leads || []).map((row) => row.id);

    const mensagemQuery = supabase
      .from("mensagens")
      .delete({ count: "exact" })
      .eq("tenant_id", tenant.tenant_id);
    if (telefone) mensagemQuery.eq("telefone", telefone);
    const { count: mensagensRemovidas, error: mensagensError } = await mensagemQuery;
    if (mensagensError) throw mensagensError;

    const conversaQuery = supabase
      .from("conversas")
      .delete({ count: "exact" })
      .eq("tenant_id", tenant.tenant_id);
    if (contatoIds.length > 0) conversaQuery.in("contato_id", contatoIds);
    const { count: conversasRemovidas, error: conversasError } = await conversaQuery;
    if (conversasError) throw conversasError;

    let leadsRemovidos = 0;
    if (!telefone || leadIds.length > 0) {
      const leadDeleteQuery = supabase
        .from("leads")
        .delete({ count: "exact" })
        .eq("tenant_id", tenant.tenant_id);
      if (leadIds.length > 0) leadDeleteQuery.in("id", leadIds);
      const { count, error: leadsError } = await leadDeleteQuery;
      if (leadsError) throw leadsError;
      leadsRemovidos = count || 0;
    }

    const contatoDeleteQuery = supabase
      .from("contatos")
      .delete({ count: "exact" })
      .eq("tenant_id", tenant.tenant_id);
    if (telefone) contatoDeleteQuery.eq("telefone", telefone);
    const { count: contatosRemovidos, error: contatosError } = await contatoDeleteQuery;
    if (contatosError) throw contatosError;

    await supabase.from("memoria_reset_auditoria").insert({
      tenant_id: tenant.tenant_id,
      user_id: user?.id || null,
      telefone: telefone || null,
      escopo: telefone ? "telefone" : "tenant",
      mensagens_removidas: mensagensRemovidas || 0,
      conversas_removidas: conversasRemovidas || 0,
      leads_removidos: leadsRemovidos,
      contatos_removidos: contatosRemovidos || 0,
      motivo,
    });

    return NextResponse.json({
      ok: true,
      telefone: telefone || null,
      removidos: {
        mensagens: mensagensRemovidas || 0,
        conversas: conversasRemovidas || 0,
        leads: leadsRemovidos,
        contatos: contatosRemovidos || 0,
      },
      preservado: "webhook_capturas",
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Erro ao resetar conversas.";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
