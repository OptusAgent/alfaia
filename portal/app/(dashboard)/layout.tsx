import Link from "next/link";
import { redirect } from "next/navigation";
import { getUserTenants, getActiveTenant } from "@/lib/tenant";
import { hasPermission } from "@/lib/permissions";
import { NAV_ITEMS } from "@/lib/nav";
import { TenantSwitcher } from "./tenant-switcher";
import { signOut } from "./sign-out-action";

// Shell autenticado (story 1.3). Nenhum módulo tem lógica de negócio própria
// aqui — só roteamento, navegação condicionada por permissão (Task 3, AC 2)
// e o seletor de tenant ativo (Task 2/5, AC 5). Ver docs/stories/1.3.story.md.
export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const memberships = await getUserTenants();

  if (memberships.length === 0) {
    // Usuário autenticado mas sem nenhum tenant_membros — não deveria
    // acontecer em uso normal, mas é um estado real possível (ex.: conta
    // criada antes do onboarding, story 8.3). Falha de forma legível, não
    // com uma tela em branco.
    return (
      <main className="flex min-h-screen items-center justify-center p-6 text-center">
        <p className="text-neutral-600">
          Sua conta ainda não está associada a nenhum tenant. Fale com o
          operador responsável pelo seu acesso.
        </p>
      </main>
    );
  }

  const activeTenant = await getActiveTenant();
  if (!activeTenant) redirect("/login");

  const visibility = await Promise.all(
    NAV_ITEMS.map(async (item) => {
      const checks = await Promise.all(
        item.anyOf.map((c) => hasPermission(activeTenant.tenant_id, c.recurso, c.acao)),
      );
      return checks.some(Boolean);
    }),
  );
  const visibleNavItems = NAV_ITEMS.filter((_, i) => visibility[i]);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b border-neutral-200 bg-white px-4 py-3">
        <div className="flex items-center gap-6">
          <span className="text-base font-semibold text-neutral-900">ALFAIA</span>
          <nav aria-label="Navegação principal">
            <ul className="flex flex-wrap gap-1">
              {visibleNavItems.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="block rounded-md px-3 py-1.5 text-sm font-medium text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-900"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <TenantSwitcher memberships={memberships} activeTenantId={activeTenant.tenant_id} />
          <form action={signOut}>
            <button
              type="submit"
              className="rounded-md px-2 py-1 text-sm text-neutral-500 hover:text-neutral-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-900"
            >
              Sair
            </button>
          </form>
        </div>
      </header>

      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
