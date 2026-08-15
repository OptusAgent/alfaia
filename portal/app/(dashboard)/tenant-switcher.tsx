"use client";

import { useRef } from "react";
import type { TenantMembership } from "@/lib/tenant";
import { switchTenant } from "./switch-tenant-action";

export function TenantSwitcher({
  memberships,
  activeTenantId,
}: {
  memberships: TenantMembership[];
  activeTenantId: string;
}) {
  const formRef = useRef<HTMLFormElement>(null);

  // Só um tenant: nada para trocar, mostra o nome como texto (AC 5 fala em
  // seletor "para usuários multi-tenant" — com 1 só, o seletor seria ruído).
  if (memberships.length <= 1) {
    return (
      <span
        className="text-sm font-medium"
        style={{ color: "var(--text-secondary)" }}
      >
        {memberships[0]?.nome ?? "—"}
      </span>
    );
  }

  return (
    <form ref={formRef} action={switchTenant}>
      <label htmlFor="tenant_id" className="sr-only">
        Tenant ativo
      </label>
      <select
        id="tenant_id"
        name="tenant_id"
        defaultValue={activeTenantId}
        onChange={() => formRef.current?.requestSubmit()}
        className="glass-select w-full"
      >
        {memberships.map((m) => (
          <option key={m.tenant_id} value={m.tenant_id}>
            {m.nome}
          </option>
        ))}
      </select>
    </form>
  );
}
