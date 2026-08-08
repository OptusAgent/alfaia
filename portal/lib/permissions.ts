import "server-only";
import { createClient } from "@/lib/supabase/server";

// Guard de autorização do Portal. Chama a MESMA função usada pela RLS no
// banco (public.has_permission, story 1.2) — nunca reimplementar a matriz
// de §4.2 em JS (coding-standards.md §3: "usar o helper has_permission
// também no guard de rota, não só na policy de RLS").
export async function hasPermission(
  tenantId: string,
  recurso: string,
  acao: string,
): Promise<boolean> {
  const supabase = await createClient();

  const { data, error } = await supabase.rpc("has_permission", {
    p_tenant_id: tenantId,
    p_recurso: recurso,
    p_acao: acao,
  });

  if (error) {
    // Nega por padrão em caso de erro — nunca abre acesso por falha de infra.
    console.error("has_permission RPC error:", error.message);
    return false;
  }

  return data === true;
}
