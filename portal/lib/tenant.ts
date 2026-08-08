import "server-only";
import { cookies } from "next/headers";
import { createClient } from "@/lib/supabase/server";

export const ACTIVE_TENANT_COOKIE = "alfaia_active_tenant";

export type TenantMembership = {
  tenant_id: string;
  nome: string;
  slug: string;
  papel: "dono" | "atendente" | "operador";
};

// Decisão de implementação (@dev): o PRD (AC 5 da story 1.2) exige que a troca
// de tenant ativo mude o contexto de RLS sem exigir novo login, mas não
// especifica o mecanismo. Implementado como cookie httpOnly
// (`alfaia_active_tenant`) lido a cada requisição — RLS em si é sempre por
// linha (tenant_id da linha, não da sessão), o cookie só decide QUAL tenant
// as telas e chamadas atuais devem filtrar quando o usuário pertence a mais
// de um.
export async function getUserTenants(): Promise<TenantMembership[]> {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return [];

  // BUG encontrado em teste manual: a policy de RLS de tenant_membros libera
  // leitura de QUALQUER linha cujo tenant_id esteja entre os tenants do
  // usuário atual (é assim que ela precisa ser, para permitir uma futura
  // tela de "membros do tenant") — ou seja, sem este .eq explícito, esta
  // função retorna a associação de TODOS os colegas do mesmo tenant, não só
  // a do próprio usuário. RLS aqui restringe por TENANT, não por LINHA; o
  // filtro por "é a minha associação" precisa ser feito na query mesmo.
  const { data, error } = await supabase
    .from("tenant_membros")
    .select("tenant_id, papel, tenants(nome, slug)")
    .eq("user_id", user.id);

  if (error || !data) return [];

  return data
    .filter((row) => row.tenants)
    .map((row) => {
      const tenant = Array.isArray(row.tenants) ? row.tenants[0] : row.tenants;
      return {
        tenant_id: row.tenant_id,
        papel: row.papel,
        nome: tenant.nome,
        slug: tenant.slug,
      };
    });
}

export async function getActiveTenant(): Promise<TenantMembership | null> {
  const memberships = await getUserTenants();
  if (memberships.length === 0) return null;

  const cookieStore = await cookies();
  const activeId = cookieStore.get(ACTIVE_TENANT_COOKIE)?.value;

  const active = memberships.find((m) => m.tenant_id === activeId);
  return active ?? memberships[0];
}
