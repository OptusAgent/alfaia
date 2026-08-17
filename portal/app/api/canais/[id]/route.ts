import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function PATCH(req: Request, context: RouteContext) {
  try {
    const { id } = await context.params;
    const body = await req.json();
    const supabase = await createClient();

    const updates: Record<string, unknown> = {
      editado_em: new Date().toISOString(),
    };

    if (typeof body.nome === "string") {
      updates.nome = body.nome.trim();
    }

    if (typeof body.telefone === "string") {
      const telefone = body.telefone.replace(/\D/g, "");
      updates.telefone = telefone || null;
    }

    if (typeof body.status === "string") {
      updates.status = body.status;
    }

    const { data, error } = await supabase
      .from("canais")
      .update(updates)
      .eq("id", id)
      .is("excluido_em", null)
      .select("*")
      .single();

    if (error) {
      throw error;
    }

    return NextResponse.json({ ok: true, canal: data });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Erro desconhecido";
    return NextResponse.json({ error: msg }, { status: 400 });
  }
}

export async function DELETE(_req: Request, context: RouteContext) {
  try {
    const { id } = await context.params;
    const supabase = await createClient();

    const { error } = await supabase
      .from("canais")
      .update({
        ativo: false,
        excluido_em: new Date().toISOString(),
        editado_em: new Date().toISOString(),
      })
      .eq("id", id);

    if (error) {
      throw error;
    }

    return NextResponse.json({ ok: true });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Erro desconhecido";
    return NextResponse.json({ error: msg }, { status: 400 });
  }
}
