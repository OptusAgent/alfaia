import { NextResponse } from "next/server";
import { getActiveTenant } from "@/lib/tenant";

export async function GET() {
  const tenant = await getActiveTenant();

  if (!tenant) {
    return NextResponse.json({ error: "Tenant ativo nao encontrado." }, { status: 401 });
  }

  return NextResponse.json({
    tenant_id: tenant.tenant_id,
    nome: tenant.nome,
    papel: tenant.papel,
  });
}
