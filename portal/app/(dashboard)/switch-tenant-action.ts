"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ACTIVE_TENANT_COOKIE, getUserTenants } from "@/lib/tenant";

export async function switchTenant(formData: FormData) {
  const tenantId = String(formData.get("tenant_id") ?? "");

  // Nunca confiar no valor do form sem checar que o usuário é de fato membro
  // do tenant solicitado (defesa em profundidade — RLS também bloquearia
  // qualquer leitura cruzada, mas o cookie não deve nem ser setado errado).
  const memberships = await getUserTenants();
  const isMember = memberships.some((m) => m.tenant_id === tenantId);
  if (!isMember) return;

  const cookieStore = await cookies();
  cookieStore.set(ACTIVE_TENANT_COOKIE, tenantId, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
  });

  redirect("/kanban");
}
