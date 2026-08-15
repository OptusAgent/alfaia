import Link from "next/link";
import { redirect } from "next/navigation";
import { getUserTenants, getActiveTenant } from "@/lib/tenant";
import { hasPermission } from "@/lib/permissions";
import { NAV_ITEMS } from "@/lib/nav";
import { TenantSwitcher } from "./tenant-switcher";
import { signOut } from "./sign-out-action";
import { createClient } from "@/lib/supabase/server";
import {
  LayoutGrid,
  MessageSquare,
  CalendarDays,
  Users,
  Settings,
  LogOut,
  Zap,
} from "lucide-react";

const NAV_ICONS: Record<string, React.ReactNode> = {
  "/kanban": <LayoutGrid className="h-4 w-4" />,
  "/conversas": <MessageSquare className="h-4 w-4" />,
  "/agenda": <CalendarDays className="h-4 w-4" />,
  "/contatos": <Users className="h-4 w-4" />,
  "/configuracoes": <Settings className="h-4 w-4" />,
};

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  // Sem middleware, a proteção das rotas privadas precisa acontecer aqui
  if (!user) {
    redirect("/login");
  }

  const memberships = await getUserTenants();

  if (memberships.length === 0) {
    return (
      <main
        className="flex min-h-screen items-center justify-center p-6 text-center"
        style={{ backgroundColor: "var(--bg-primary)" }}
      >
        <div className="glass-card-elevated max-w-md p-8">
          <h2
            className="font-display text-xl font-bold mb-2"
            style={{ color: "var(--text-primary)" }}
          >
            Conta Sem Organização
          </h2>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Sua conta ainda não está associada a nenhum tenant. Fale com o
            operador responsável pelo seu acesso.
          </p>
          <form action={signOut} className="mt-4">
            <button
              type="submit"
              className="text-sm font-medium hover:underline"
              style={{ color: "var(--accent-primary)" }}
            >
              Sair da conta
            </button>
          </form>
        </div>
      </main>
    );
  }

  const activeTenant = await getActiveTenant();
  if (!activeTenant) redirect("/login");

  const visibility = await Promise.all(
    NAV_ITEMS.map(async (item) => {
      const checks = await Promise.all(
        item.anyOf.map((c) =>
          hasPermission(activeTenant.tenant_id, c.recurso, c.acao)
        )
      );
      return checks.some(Boolean);
    })
  );
  const visibleNavItems = NAV_ITEMS.filter((_, i) => visibility[i]);

  return (
    <div className="flex min-h-screen" style={{ backgroundColor: "var(--bg-primary)", color: "var(--text-primary)" }}>
      {/* ━━━ Sidebar ━━━ */}
      <aside
        className="w-64 flex flex-col h-screen sticky top-0 shrink-0 z-20"
        style={{
          backgroundColor: "var(--bg-secondary)",
          borderRight: "1px solid rgba(255, 255, 255, 0.06)",
        }}
      >
        {/* Logo Header */}
        <div
          className="p-5"
          style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.06)" }}
        >
          <div className="flex items-center gap-3">
            <div
              className="flex h-9 w-9 items-center justify-center rounded-xl"
              style={{
                background: "linear-gradient(135deg, var(--accent-primary) 0%, #059669 100%)",
                boxShadow: "var(--shadow-glow-teal)",
              }}
            >
              <svg className="h-5 w-5 fill-current text-black" viewBox="0 0 24 24">
                <path d="M12 2L2 19h20L12 2zm0 4l6.5 11h-13L12 6z" />
              </svg>
            </div>
            <div>
              <h1
                className="font-display text-xl font-semibold tracking-wide leading-none"
                style={{ color: "var(--text-primary)" }}
              >
                ALFAIA
              </h1>
              <span
                className="font-mono text-[9px] uppercase tracking-widest font-semibold block mt-0.5"
                style={{ color: "var(--accent-primary)" }}
              >
                Atendimento + CRM
              </span>
            </div>
          </div>
        </div>

        {/* User Card */}
        <div
          className="mx-3 my-3 p-3 rounded-xl flex items-center gap-3"
          style={{
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.06)",
          }}
        >
          <div className="relative">
            <div
              className="h-9 w-9 rounded-full flex items-center justify-center text-xs font-bold"
              style={{
                background: "linear-gradient(135deg, var(--accent-primary) 0%, #059669 100%)",
                color: "#000",
              }}
            >
              {user.email?.substring(0, 2).toUpperCase()}
            </div>
            <span
              className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full"
              style={{
                backgroundColor: "var(--accent-primary)",
                border: "2px solid var(--bg-secondary)",
              }}
            />
          </div>
          <div className="min-w-0 flex-1">
            <b
              className="block text-xs font-semibold truncate"
              style={{ color: "var(--text-primary)" }}
            >
              {user.email}
            </b>
            <span
              className="font-mono text-[10px] block truncate"
              style={{ color: "var(--text-muted)" }}
            >
              {activeTenant.papel.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="px-3 py-2 flex-1 overflow-y-auto space-y-0.5" aria-label="Navegação principal">
          <div
            className="font-mono text-[9px] uppercase tracking-widest px-3 pt-3 pb-2 font-semibold"
            style={{ color: "var(--text-muted)" }}
          >
            Módulos
          </div>
          {visibleNavItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all group"
              style={{ color: "var(--text-secondary)" }}
            >
              <span
                className="group-hover:text-[var(--accent-primary)] transition-colors"
                style={{ color: "var(--text-muted)" }}
              >
                {NAV_ICONS[item.href] || <Zap className="h-4 w-4" />}
              </span>
              <span className="group-hover:text-[var(--text-primary)] transition-colors">
                {item.label}
              </span>
            </Link>
          ))}
        </nav>

        {/* Footer */}
        <div
          className="p-3 space-y-2"
          style={{
            borderTop: "1px solid rgba(255, 255, 255, 0.06)",
            background: "rgba(0, 0, 0, 0.15)",
          }}
        >
          <div className="text-xs px-1">
            <span
              className="font-mono text-[9px] uppercase tracking-widest block mb-1"
              style={{ color: "var(--text-muted)" }}
            >
              Tenant Ativo
            </span>
            <TenantSwitcher
              memberships={memberships}
              activeTenantId={activeTenant.tenant_id}
            />
          </div>

          <form action={signOut}>
            <button
              type="submit"
              className="glass-btn glass-btn-ghost w-full text-xs gap-2 py-2 cursor-pointer"
            >
              <LogOut className="h-3.5 w-3.5" />
              Encerrar Sessão
            </button>
          </form>
        </div>
      </aside>

      {/* ━━━ Main Content ━━━ */}
      <main className="flex-1 min-w-0 flex flex-col min-h-screen">
        <div className="flex-1 p-6 lg:p-8 max-w-[1600px] w-full mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
