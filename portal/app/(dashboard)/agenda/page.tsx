"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Badge } from "@/app/components/ui/Badge";
import { Calendar, Filter, RefreshCw, Info, ExternalLink, Clock, Tag } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

interface Agendamento {
  id: string;
  wl_agendamento_id: string;
  lead_id: string | null;
  tipo: string;
  data: string;
  hora: string;
  cliente_nome: string;
  cliente_telefone: string;
  produto_ref?: string | null;
  origem: "automacao" | "loja";
  status: string;
}

function formatarDataLocal(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function calcularIntervalo(periodo: "dia" | "semana" | "mes" | "custom", inicioCustom: string, fimCustom: string) {
  const hoje = new Date();
  if (periodo === "dia") {
    const d = formatarDataLocal(hoje);
    return { inicio: d, fim: d };
  }
  if (periodo === "semana") {
    const diaSemana = hoje.getDay();
    const inicioSemana = new Date(hoje);
    inicioSemana.setDate(hoje.getDate() - diaSemana);
    const fimSemana = new Date(inicioSemana);
    fimSemana.setDate(inicioSemana.getDate() + 6);
    return { inicio: formatarDataLocal(inicioSemana), fim: formatarDataLocal(fimSemana) };
  }
  if (periodo === "mes") {
    const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    const fimMes = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
    return { inicio: formatarDataLocal(inicioMes), fim: formatarDataLocal(fimMes) };
  }
  return { inicio: inicioCustom || formatarDataLocal(hoje), fim: fimCustom || formatarDataLocal(hoje) };
}

export default function AgendaPage() {
  const [periodo, setPeriodo] = useState<"dia" | "semana" | "mes" | "custom">("mes");
  const [filtroOrigem, setFiltroOrigem] = useState<"todas" | "automacao" | "loja">("todas");
  const [inicioCustom, setInicioCustom] = useState("");
  const [fimCustom, setFimCustom] = useState("");
  const [tenantId, setTenantId] = useState("");
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
  const supabase = useMemo(() => createClient(), []);

  const { inicio, fim } = useMemo(
    () => calcularIntervalo(periodo, inicioCustom, fimCustom),
    [periodo, inicioCustom, fimCustom]
  );

  useEffect(() => {
    let mounted = true;

    async function carregar() {
      setCarregando(true);
      setErro("");

      const resTenant = await fetch("/api/tenant/active", { cache: "no-store" });
      if (!resTenant.ok) {
        if (mounted) {
          setTenantId("");
          setAgendamentos([]);
          setCarregando(false);
        }
        return;
      }
      const dataTenant = await resTenant.json();
      const activeTenantId = String(dataTenant.tenant_id || "");
      if (!mounted) return;
      setTenantId(activeTenantId);

      if (!activeTenantId) {
        setAgendamentos([]);
        setCarregando(false);
        return;
      }

      let query = supabase
        .from("agendamentos")
        .select("id, wl_agendamento_id, lead_id, tipo, data, hora, cliente_nome, cliente_telefone, produto_ref, origem, status")
        .eq("tenant_id", activeTenantId)
        .eq("status", "ativo")
        .gte("data", inicio)
        .lte("data", fim)
        .order("data", { ascending: true })
        .order("hora", { ascending: true });

      if (filtroOrigem !== "todas") {
        query = query.eq("origem", filtroOrigem);
      }

      const { data, error } = await query;
      if (!mounted) return;

      if (error) {
        setErro("Não foi possível carregar a agenda agora.");
        setAgendamentos([]);
      } else {
        setAgendamentos((data as Agendamento[]) || []);
      }
      setCarregando(false);
    }

    void carregar();
    return () => {
      mounted = false;
    };
  }, [supabase, inicio, fim, filtroOrigem]);

  const handleSync = async () => {
    if (!tenantId) return;
    setIsSyncing(true);
    setErro("");
    try {
      const params = new URLSearchParams({ tenant_id: tenantId, inicio, fim });
      const res = await fetch(`/api/agenda/sync?${params.toString()}`, { method: "POST" });
      if (!res.ok) {
        setErro("Falha ao sincronizar com a WebLocação agora.");
      } else {
        const { data } = await supabase
          .from("agendamentos")
          .select("id, wl_agendamento_id, lead_id, tipo, data, hora, cliente_nome, cliente_telefone, produto_ref, origem, status")
          .eq("tenant_id", tenantId)
          .eq("status", "ativo")
          .gte("data", inicio)
          .lte("data", fim)
          .order("data", { ascending: true })
          .order("hora", { ascending: true });
        setAgendamentos((data as Agendamento[]) || []);
      }
    } catch {
      setErro("Falha ao sincronizar com a WebLocação agora.");
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <section aria-labelledby="agenda-title" className="space-y-5">
      <div
        className="flex items-center gap-3 rounded-[8px] p-4"
        style={{
          background: "var(--slate-l)",
          border: "1px solid rgba(74, 107, 132, 0.2)",
        }}
      >
        <Info className="h-5 w-5 flex-shrink-0" style={{ color: "var(--slate)" }} />
        <div className="text-[12.3px]" style={{ color: "var(--ink2)" }}>
          Visualização apenas. Remarcar, cancelar ou criar manualmente é feito no portal da WebLocação.
        </div>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1
            id="agenda-title"
            className="section-heading flex items-center gap-2"
            style={{ color: "var(--text-primary)" }}
          >
            <Calendar className="h-6 w-6" style={{ color: "var(--accent-primary)" }} />
            Agenda
          </h1>
          <p className="section-subtitle">
            Provas e atendimentos, leitura da WebLocação.
          </p>
        </div>

        <button
          id="btn-sync-agenda"
          onClick={handleSync}
          disabled={isSyncing || !tenantId}
          className="glass-btn glass-btn-primary"
        >
          <RefreshCw className={`h-4 w-4 ${isSyncing ? "animate-spin" : ""}`} />
          {isSyncing ? "Sincronizando..." : "Sincronizar Agora"}
        </button>
      </div>

      <div
        className="glass-card flex flex-wrap items-center justify-between gap-4 p-4"
      >
        <div
          className="flex items-center gap-1 rounded-[8px] border p-1 text-xs font-semibold"
          style={{ background: "var(--c2)", borderColor: "var(--line)" }}
        >
          {(["dia", "semana", "mes", "custom"] as const).map((p) => (
            <button
              key={p}
              id={`btn-periodo-${p}`}
              onClick={() => setPeriodo(p)}
              className="rounded-md px-3 py-1.5 capitalize transition-all"
              style={{
                background: periodo === p ? "var(--accent-primary-muted)" : "transparent",
                color: periodo === p ? "var(--ink)" : "var(--text-muted)",
              }}
            >
              {p === "mes" ? "Mês" : p === "custom" ? "Customizado" : p}
            </button>
          ))}
        </div>

        {periodo === "custom" && (
          <div className="flex items-center gap-2 text-xs">
            <input
              type="date"
              value={inicioCustom}
              onChange={(e) => setInicioCustom(e.target.value)}
              className="glass-select"
              style={{ width: "auto" }}
            />
            <span style={{ color: "var(--text-muted)" }}>até</span>
            <input
              type="date"
              value={fimCustom}
              onChange={(e) => setFimCustom(e.target.value)}
              className="glass-select"
              style={{ width: "auto" }}
            />
          </div>
        )}

        <div className="flex items-center gap-3">
          <Filter className="h-4 w-4" style={{ color: "var(--text-muted)" }} />
          <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
            Origem:
          </span>
          <select
            id="select-filtro-origem"
            value={filtroOrigem}
            onChange={(e) => setFiltroOrigem(e.target.value as typeof filtroOrigem)}
            className="glass-select"
            style={{ width: "auto" }}
          >
            <option value="todas">Todas as origens</option>
            <option value="automacao">Automação (IA)</option>
            <option value="loja">Balcão / Loja ERP</option>
          </select>
        </div>
      </div>

      {erro && (
        <div
          className="rounded-[8px] p-3 text-[12.3px]"
          style={{ background: "rgba(200, 60, 60, 0.1)", border: "1px solid rgba(200, 60, 60, 0.3)", color: "var(--ink2)" }}
        >
          {erro}
        </div>
      )}

      <div
        className="glass-card overflow-hidden"
        style={{
          boxShadow: "var(--shadow-md)",
        }}
      >
        <table className="dark-table">
          <thead>
            <tr>
              <th>Data e Hora</th>
              <th>Cliente / Lead</th>
              <th>Tipo</th>
              <th>Produto Ref</th>
              <th>Origem</th>
              <th className="text-right">Ação</th>
            </tr>
          </thead>
          <tbody>
            {carregando && (
              <tr>
                <td colSpan={6} className="text-center" style={{ color: "var(--text-muted)" }}>
                  Carregando agenda...
                </td>
              </tr>
            )}
            {!carregando && agendamentos.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center" style={{ color: "var(--text-muted)" }}>
                  Nenhum agendamento neste período.
                </td>
              </tr>
            )}
            {!carregando && agendamentos.map((ag) => (
              <tr key={ag.id}>
                <td className="font-medium" style={{ color: "var(--text-primary)" }}>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" style={{ color: "var(--text-muted)" }} />
                    <span>{ag.data} às {ag.hora}</span>
                  </div>
                </td>
                <td>
                  <div className="font-semibold" style={{ color: "var(--text-primary)" }}>
                    {ag.cliente_nome}
                  </div>
                  <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                    {ag.cliente_telefone}
                  </div>
                </td>
                <td className="capitalize">
                  <span
                    className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium"
                    style={{
                      background: "var(--line)",
                      color: "var(--text-secondary)",
                    }}
                  >
                    <Tag className="h-3 w-3" style={{ color: "var(--text-muted)" }} />
                    {ag.tipo}
                  </span>
                </td>
                <td className="font-mono text-xs">
                  {ag.produto_ref || "—"}
                </td>
                <td>
                  {ag.origem === "automacao" ? (
                    <Badge variant="success">Automação</Badge>
                  ) : (
                    <Badge variant="neutral">Loja / ERP</Badge>
                  )}
                </td>
                <td className="text-right">
                  {ag.lead_id ? (
                    <Link
                      href={`/conversas?lead_id=${ag.lead_id}`}
                      className="inline-flex items-center gap-1 text-xs font-semibold hover:underline"
                      style={{ color: "var(--accent-primary)" }}
                    >
                      Ver Lead <ExternalLink className="h-3.5 w-3.5" />
                    </Link>
                  ) : (
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
