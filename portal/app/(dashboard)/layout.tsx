import { redirect } from "next/navigation";
import { getUserTenants, getActiveTenant } from "@/lib/tenant";
import { hasPermission } from "@/lib/permissions";
import { NAV_ITEMS } from "@/lib/nav";
import { TenantSwitcher } from "./tenant-switcher";
import { signOut } from "./sign-out-action";
import { createClient } from "@/lib/supabase/server";
import { DashboardNavLink } from "./dashboard-nav-link";
import {
  LayoutGrid,
  MessageSquare,
  CalendarDays,
  Users,
  Settings,
  LogOut,
  Zap,
  Bell,
  Search,
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
    <div className="atelier-shell">
      <aside className="atelier-sidebar">
        <div className="flex items-center gap-[9px] px-1.5 pb-[22px]">
          <div className="flex items-center gap-[9px]">
            <div className="atelier-logo-mark">
              <svg width="30" height="30" viewBox="0 0 40 40" aria-hidden="true">
                <circle cx="20" cy="20" r="18" fill="none" stroke="currentColor" strokeWidth="2" opacity=".45" />
                <path d="M8 25c5 0 5-10 10-10s5 10 10 10 4-4 4-4" fill="none" stroke="currentColor" strokeWidth="3.6" strokeLinecap="round" />
                <path d="M8 17c5 0 5-6 10-6" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" opacity=".55" />
              </svg>
            </div>
            <div>
              <h1
                className="font-display text-xl font-extrabold leading-none tracking-[-0.02em]"
                style={{ color: "#fff" }}
              >
                ALFAIA
              </h1>
              <span
                className="mt-1 block text-[8px] font-bold uppercase tracking-[0.3em]"
                style={{ color: "var(--teal)" }}
              >
                RETAGUARDA
              </span>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-[9px] py-2" aria-label="Navegação principal">
          <div className="atelier-nav-section">Loja</div>
          {visibleNavItems.map((item) => (
            <DashboardNavLink
              key={item.href}
              href={item.href}
              icon={NAV_ICONS[item.href] || <Zap className="h-4 w-4" />}
              label={item.label}
            />
          ))}
        </nav>

        <div className="my-3 mx-1.5 border-t" style={{ borderColor: "rgba(255,255,255,.12)" }} />

        <div className="atelier-nav-section">Escritório</div>
        <div className="px-[9px]">
          <DashboardNavLink href="/observabilidade" icon={<Zap className="h-4 w-4" />} label="Observabilidade" />
        </div>

        <div className="fluir-countdown">
          <div className="label">SLA atendimento</div>
          <div className="number">2h</div>
          <div className="desc">janela ideal para responder leads quentes</div>
          <div className="bar"><i /></div>
        </div>

        <div className="mt-3 space-y-3">
          <div className="atelier-channel">
            <span className="atelier-channel-dot" />
            <div className="min-w-0 flex-1 text-left">
              <b className="block text-[12px] leading-tight">WhatsApp ativo</b>
              <small className="block truncate text-[10.5px]" style={{ color: "rgba(255,255,255,.66)" }}>
                Meta Cloud API
              </small>
            </div>
          </div>

          <div className="px-1 text-xs text-white">
            <span
              className="mb-1 block text-[9px] font-bold uppercase tracking-[0.18em]"
              style={{ color: "rgba(255,255,255,.38)" }}
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
              className="w-full cursor-pointer rounded-[12px] border px-3 py-2 text-xs font-bold text-white transition hover:bg-white/10"
              style={{ borderColor: "rgba(255,255,255,.14)" }}
            >
              <LogOut className="h-3.5 w-3.5" />
              Encerrar Sessão
            </button>
          </form>
        </div>
      </aside>

      <main className="atelier-main">
        <header className="atelier-topbar">
          <div>
            <h2 className="font-display text-[25px] font-extrabold leading-tight tracking-[-0.025em]" style={{ color: "var(--ink)" }}>
              Operação ALFAIA
            </h2>
            <p className="mt-0.5 text-xs" style={{ color: "var(--dim)" }}>
              Atendimento + CRM conversacional · {activeTenant.nome}
            </p>
          </div>
          <div className="ml-auto flex items-center gap-[9px]">
            <button className="grid h-[38px] w-[38px] place-items-center rounded-[12px] border bg-white transition hover:bg-[var(--mint)]" style={{ borderColor: "var(--line)", color: "var(--ink-2)" }} title="Buscar">
              <Search className="h-4 w-4" />
            </button>
            <button className="relative grid h-[38px] w-[38px] place-items-center rounded-[12px] border bg-white transition hover:bg-[var(--mint)]" style={{ borderColor: "var(--line)", color: "var(--ink-2)" }} title="Avisos">
              <Bell className="h-4 w-4" />
              <span className="absolute right-[9px] top-[8px] h-[7px] w-[7px] rounded-full border-2 border-white" style={{ background: "var(--bad)" }} />
            </button>
            <div className="hidden items-center gap-[9px] rounded-[14px] border bg-white py-[5px] pl-[5px] pr-3 sm:flex" style={{ borderColor: "var(--line)" }}>
              <div className="grid h-[30px] w-[30px] place-items-center rounded-[10px] font-display text-[11px] font-extrabold text-white" style={{ background: "var(--deep)" }}>
                {user.email?.substring(0, 2).toUpperCase()}
              </div>
              <div className="min-w-0">
                <b className="block max-w-[170px] truncate text-[12.5px] leading-tight">{user.email}</b>
                <span className="block text-[10px]" style={{ color: "var(--dim)" }}>{activeTenant.papel}</span>
              </div>
            </div>
          </div>
        </header>

        <div className="atelier-content">
          {children}
        </div>
      </main>
    </div>
  );
}
