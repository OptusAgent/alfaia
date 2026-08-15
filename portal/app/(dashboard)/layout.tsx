import Link from "next/link";
import { redirect } from "next/navigation";
import { getUserTenants, getActiveTenant } from "@/lib/tenant";
import { hasPermission } from "@/lib/permissions";
import { NAV_ITEMS } from "@/lib/nav";
import { TenantSwitcher } from "./tenant-switcher";
import { signOut } from "./sign-out-action";
import { createClient } from "@/lib/supabase/server";

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
      <main className="flex min-h-screen items-center justify-center p-6 text-center bg-[#F3F6F9]">
        <div className="max-w-md rounded-2xl border border-[#CBD5E1] bg-white p-8 shadow-sm">
          <h2 className="font-serif text-xl font-bold text-[#072F53] mb-2">Conta Sem Organização</h2>
          <p className="text-sm text-slate-600">
            Sua conta ainda não está associada a nenhum tenant. Fale com o operador responsável pelo seu acesso.
          </p>
          <form action={signOut} className="mt-4">
            <button type="submit" className="text-sm text-blue-600 hover:underline">
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
        item.anyOf.map((c) => hasPermission(activeTenant.tenant_id, c.recurso, c.acao)),
      );
      return checks.some(Boolean);
    }),
  );
  const visibleNavItems = NAV_ITEMS.filter((_, i) => visibility[i]);

  return (
    <div className="flex min-h-screen bg-[#F3F6F9] text-[#1F1B17]">
      {/* Sidebar - Exact Navy Blue Design System from /frontend */}
      <aside className="w-64 bg-gradient-to-b from-[#072F53] via-[#0E4A7B] to-[#083358] text-white flex flex-col h-screen sticky top-0 border-r border-[#1868A8]/30 shadow-xl shrink-0 z-20">
        {/* Logo Header */}
        <div className="p-5 border-b border-[#1868A8]/30">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#EBB832] to-[#A67C2E] flex items-center justify-center shadow-lg text-[#072F53] font-bold">
              <svg className="w-5 h-5 text-[#072F53] fill-current" viewBox="0 0 24 24">
                <path d="M12 2L2 19h20L12 2zm0 4l6.5 11h-13L12 6z" />
              </svg>
            </div>
            <div>
              <h1 className="font-serif text-2xl font-normal tracking-wider text-white leading-none">
                ALFAIA
              </h1>
              <span className="font-mono text-[9px] uppercase tracking-widest text-[#EBB832] font-semibold block mt-1">
                Atendimento + CRM
              </span>
            </div>
          </div>
        </div>

        {/* User Avatar Card */}
        <div className="mx-3 my-3 p-3 rounded-xl bg-white/10 backdrop-blur-md border border-white/10 flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#EBB832] to-[#F2E7D0] text-[#072F53] font-bold flex items-center justify-center text-sm shadow">
              {user.email?.substring(0, 2).toUpperCase()}
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-[#072F53]"></span>
          </div>
          <div className="min-w-0 flex-1">
            <b className="block text-xs font-semibold text-white truncate">{user.email}</b>
            <div className="flex items-center gap-0.5 mt-0.5 text-[#EBB832]">
              {[...Array(5)].map((_, i) => (
                <svg key={i} className="w-2.5 h-2.5 fill-current" viewBox="0 0 24 24">
                  <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                </svg>
              ))}
            </div>
            <span className="text-[10px] text-slate-300 font-mono block truncate">
              {activeTenant.papel.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="px-3 py-2 flex-1 overflow-y-auto space-y-1" aria-label="Navegação principal">
          <div className="font-mono text-[9px] uppercase tracking-widest text-slate-300 px-3 pt-2 pb-1 font-semibold opacity-80">
            Operação & Módulos
          </div>
          {visibleNavItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium text-slate-200 hover:bg-white/10 hover:text-white transition-all group"
            >
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        {/* Sidebar Footer / Tenant Switcher & Sign Out */}
        <div className="p-3 border-t border-[#1868A8]/30 space-y-2 bg-[#072F53]/40">
          <div className="text-xs px-1">
            <span className="font-mono text-[9px] uppercase tracking-widest text-slate-300 block mb-1">
              Loja / Tenant Ativo
            </span>
            <TenantSwitcher memberships={memberships} activeTenantId={activeTenant.tenant_id} />
          </div>

          <form action={signOut}>
            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-semibold text-white transition-all cursor-pointer border border-white/10"
            >
              Encerrar Sessão
            </button>
          </form>
        </div>
      </aside>

      {/* Main Workspace Content */}
      <main className="flex-1 min-w-0 flex flex-col min-h-screen">
        <div className="flex-1 p-6 lg:p-8 max-w-[1600px] w-full mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
