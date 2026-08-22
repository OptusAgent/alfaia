"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Radio,
  QrCode,
  CheckCircle2,
  AlertTriangle,
  Smartphone,
  ShieldCheck,
  Zap,
  RefreshCw,
  Plus,
  Phone,
  Clock3,
  Pencil,
  Trash2,
  CalendarClock,
} from "lucide-react";
import { UazapiQrModal } from "./uazapi-qr-modal";
import { Badge } from "@/app/components/ui/Badge";
import { createClient } from "@/lib/supabase/client";

interface Canal {
  id: string;
  provider: string;
  nome: string;
  ativo: boolean;
  status: string;
  qualidade: string | null;
  telefone: string | null;
  uazapi_instancia: string | null;
  ultimo_healthcheck_em: string | null;
}

interface Turno {
  id: string;
  dia_semana: number; // 0=domingo .. 6=sábado
  hora_abertura: string; // "HH:MM:SS" (Postgres time)
  hora_fechamento: string;
}

const DIAS_SEMANA = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"];

function hhmm(hora: string) {
  return hora.slice(0, 5);
}

function turnosSeSobrepoem(aInicio: string, aFim: string, bInicio: string, bFim: string) {
  return aInicio < bFim && bInicio < aFim;
}

export default function ConfiguracoesPage() {
  const [canais, setCanais] = useState<Canal[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmingChannel, setConfirmingChannel] = useState<Canal | null>(null);
  const [editingChannel, setEditingChannel] = useState<Canal | null>(null);
  const [deletingChannel, setDeletingChannel] = useState<Canal | null>(null);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [resetPhone, setResetPhone] = useState("");
  const [resetConfirm, setResetConfirm] = useState("");
  const [resettingMemory, setResettingMemory] = useState(false);
  const [resetResult, setResetResult] = useState<string | null>(null);
  const [resetError, setResetError] = useState<string | null>(null);

  const supabase = useMemo(() => createClient(), []);
  const [tenantId, setTenantId] = useState("");
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [carregandoTurnos, setCarregandoTurnos] = useState(true);
  const [erroTurnos, setErroTurnos] = useState<string | null>(null);
  const [modalTurnoAberto, setModalTurnoAberto] = useState(false);
  const [turnoEditando, setTurnoEditando] = useState<Turno | null>(null);
  const [turnoExcluindo, setTurnoExcluindo] = useState<Turno | null>(null);
  const [salvandoTurno, setSalvandoTurno] = useState(false);
  const [erroFormTurno, setErroFormTurno] = useState<string | null>(null);
  const [avisoSobreposicao, setAvisoSobreposicao] = useState<{
    dia_semana: number;
    hora_abertura: string;
    hora_fechamento: string;
  } | null>(null);

  const turnosPorDia = useMemo(() => {
    const mapa: Record<number, Turno[]> = {};
    for (const t of turnos) {
      (mapa[t.dia_semana] ||= []).push(t);
    }
    for (const dia of Object.keys(mapa)) {
      mapa[Number(dia)].sort((a, b) => a.hora_abertura.localeCompare(b.hora_abertura));
    }
    return mapa;
  }, [turnos]);

  const fetchTurnos = useCallback(async (activeTenantId: string) => {
    setCarregandoTurnos(true);
    const { data, error } = await supabase
      .from("horarios_funcionamento")
      .select("id, dia_semana, hora_abertura, hora_fechamento")
      .eq("tenant_id", activeTenantId)
      .eq("ativo", true)
      .order("dia_semana", { ascending: true })
      .order("hora_abertura", { ascending: true });

    if (error) {
      setErroTurnos("Não foi possível carregar o horário de funcionamento agora.");
      setTurnos([]);
    } else {
      setErroTurnos(null);
      setTurnos((data as Turno[]) || []);
    }
    setCarregandoTurnos(false);
  }, [supabase]);

  useEffect(() => {
    let mounted = true;
    async function iniciar() {
      const res = await fetch("/api/tenant/active", { cache: "no-store" });
      if (!res.ok || !mounted) {
        setCarregandoTurnos(false);
        return;
      }
      const data = await res.json();
      const activeTenantId = String(data.tenant_id || "");
      if (!mounted) return;
      setTenantId(activeTenantId);
      if (activeTenantId) await fetchTurnos(activeTenantId);
      else setCarregandoTurnos(false);
    }
    void iniciar();
    return () => {
      mounted = false;
    };
  }, [fetchTurnos]);

  function abrirModalCriarTurno() {
    setTurnoEditando(null);
    setErroFormTurno(null);
    setModalTurnoAberto(true);
  }

  function abrirModalEditarTurno(turno: Turno) {
    setTurnoEditando(turno);
    setErroFormTurno(null);
    setModalTurnoAberto(true);
  }

  async function salvarTurno(dados: { dia_semana: number; hora_abertura: string; hora_fechamento: string }) {
    if (!tenantId) return;
    setSalvandoTurno(true);
    setErroFormTurno(null);
    try {
      const payload = {
        tenant_id: tenantId,
        dia_semana: dados.dia_semana,
        hora_abertura: dados.hora_abertura,
        hora_fechamento: dados.hora_fechamento,
        editado_em: new Date().toISOString(),
      };
      const { error } = turnoEditando
        ? await supabase
            .from("horarios_funcionamento")
            .update(payload)
            .eq("id", turnoEditando.id)
            .eq("tenant_id", tenantId)
        : await supabase.from("horarios_funcionamento").insert(payload);

      if (error) throw error;

      setModalTurnoAberto(false);
      setTurnoEditando(null);
      setAvisoSobreposicao(null);
      await fetchTurnos(tenantId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao salvar horário.";
      setErroFormTurno(msg);
    } finally {
      setSalvandoTurno(false);
    }
  }

  function handleSubmitTurno(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const diaSemana = Number(formData.get("dia_semana"));
    const abertura = String(formData.get("hora_abertura") || "");
    const fechamento = String(formData.get("hora_fechamento") || "");

    if (!abertura || !fechamento) {
      setErroFormTurno("Informe abertura e fechamento.");
      return;
    }
    if (fechamento <= abertura) {
      setErroFormTurno("O horário de fechamento precisa ser depois do de abertura.");
      return;
    }
    setErroFormTurno(null);

    const conflita = (turnosPorDia[diaSemana] || []).some(
      (t) =>
        t.id !== turnoEditando?.id &&
        turnosSeSobrepoem(abertura, fechamento, hhmm(t.hora_abertura), hhmm(t.hora_fechamento))
    );

    if (conflita) {
      setAvisoSobreposicao({ dia_semana: diaSemana, hora_abertura: abertura, hora_fechamento: fechamento });
      return;
    }

    void salvarTurno({ dia_semana: diaSemana, hora_abertura: abertura, hora_fechamento: fechamento });
  }

  async function confirmarExcluirTurno() {
    if (!turnoExcluindo || !tenantId) return;
    setSalvandoTurno(true);
    try {
      await supabase
        .from("horarios_funcionamento")
        .delete()
        .eq("id", turnoExcluindo.id)
        .eq("tenant_id", tenantId);
      setTurnoExcluindo(null);
      await fetchTurnos(tenantId);
    } finally {
      setSalvandoTurno(false);
    }
  }

  async function fetchCanais() {
    try {
      const res = await fetch("/api/canais");
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Erro ao carregar canais.");
      }

      setCanais(data.canais || []);
      setLoadError(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao carregar canais.";
      setLoadError(msg);
      setCanais([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchCanais();

    const interval = window.setInterval(() => {
      fetchCanais();
    }, 12000);

    return () => window.clearInterval(interval);
  }, []);

  async function handleToggleAtivo(canal: Canal) {
    if (canal.ativo) return; // Já está ativo
    setConfirmingChannel(canal);
  }

  async function confirmSwitchChannel() {
    if (!confirmingChannel) return;
    try {
      await fetch("/api/canais", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ canalId: confirmingChannel.id, ativar: true }),
      });
      await fetchCanais();
    } catch {
      //
    } finally {
      setConfirmingChannel(null);
    }
  }

  async function handleSalvarEdicao(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!editingChannel) return;

    const formData = new FormData(e.currentTarget);
    setSaving(true);

    try {
      const res = await fetch(`/api/canais/${editingChannel.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nome: String(formData.get("nome") || ""),
          telefone: String(formData.get("telefone") || ""),
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Erro ao salvar instância");
      }

      setEditingChannel(null);
      await fetchCanais();
    } catch {
      //
    } finally {
      setSaving(false);
    }
  }

  async function confirmDeleteChannel() {
    if (!deletingChannel) return;

    setSaving(true);
    try {
      await fetch(`/api/canais/${deletingChannel.id}`, {
        method: "DELETE",
      });
      setDeletingChannel(null);
      await fetchCanais();
    } catch {
      //
    } finally {
      setSaving(false);
    }
  }

  async function handleResetConversas(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setResettingMemory(true);
    setResetResult(null);
    setResetError(null);

    try {
      const res = await fetch("/api/conversas/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          telefone: resetPhone,
          confirmacao: resetConfirm,
          motivo: "Reset manual em Configuracoes",
        }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Erro ao resetar conversas.");
      }

      const removidos = data.removidos || {};
      setResetResult(
        `Removido: ${removidos.mensagens || 0} mensagens, ${removidos.conversas || 0} conversas, ${removidos.leads || 0} leads e ${removidos.contatos || 0} contatos.`
      );
      setResetConfirm("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao resetar conversas.";
      setResetError(msg);
    } finally {
      setResettingMemory(false);
    }
  }

  function formatPhone(phone?: string | null) {
    if (!phone) return "Telefone não informado";
    return phone.replace(/^55(\d{2})(\d{5})(\d{4})$/, "+55 ($1) $2-$3");
  }

  function formatLastCheck(value?: string | null) {
    if (!value) return "Sem healthcheck";
    return new Intl.DateTimeFormat("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
      day: "2-digit",
      month: "2-digit",
    }).format(new Date(value));
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div
        className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6"
        style={{ borderBottom: "1px solid var(--line)" }}
      >
        <div>
          <h1
            className="font-display text-3xl font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            Configurações da Conta
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
            Gestão de Canais de Comunicação, Automações e Parâmetros Operacionais.
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="glass-btn glass-btn-primary"
        >
          <Plus className="h-4 w-4" />
          <span>Nova Instância UAZAPI (QR Code)</span>
        </button>
      </div>

      {/* Rule Alert */}
      <div className="glass-card p-5">
        <div className="flex items-start gap-4">
          <div
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
            style={{
              background: "var(--accent-primary-muted)",
            }}
          >
            <Radio className="h-5 w-5" style={{ color: "var(--accent-primary)" }} />
          </div>
          <div className="space-y-1">
            <h3
              className="font-display text-lg font-bold"
              style={{ color: "var(--text-primary)" }}
            >
              Regra de Seleção de Canal
            </h3>
            <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              Conforme PRD §14.3, exatamente <strong>um canal</strong> pode
              estar ativo por tenant de cada vez. A troca de canal vale a partir
              da <strong>próxima mensagem processada</strong> e todo o histórico
              é mantido intacto.
            </p>
          </div>
        </div>
      </div>

      {/* Test Tools */}
      <form onSubmit={handleResetConversas} className="glass-card p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-xl space-y-1">
            <h3
              className="font-display text-lg font-bold"
              style={{ color: "var(--text-primary)" }}
            >
              Resetar Conversas e Memória
            </h3>
            <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              Remove conversas, mensagens, leads e contatos criados pelo atendimento
              para reiniciar testes. As capturas brutas de webhook são preservadas.
            </p>
          </div>

          <div className="grid w-full gap-3 md:grid-cols-[minmax(180px,1fr)_160px_auto] lg:w-auto">
            <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
              Telefone opcional
              <input
                value={resetPhone}
                onChange={(event) => setResetPhone(event.target.value)}
                placeholder="558599173321"
                className="glass-input mt-1.5"
              />
            </label>
            <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
              Confirmação
              <input
                value={resetConfirm}
                onChange={(event) => setResetConfirm(event.target.value)}
                placeholder="RESETAR"
                className="glass-input mt-1.5"
              />
            </label>
            <button
              type="submit"
              disabled={resettingMemory}
              className="glass-btn glass-btn-ghost self-end"
              style={{ color: "var(--accent-coral)" }}
            >
              <Trash2 className="h-4 w-4" />
              <span>{resettingMemory ? "Resetando..." : "Resetar"}</span>
            </button>
          </div>
        </div>

        {(resetResult || resetError) && (
          <div
            className="mt-4 rounded-lg px-4 py-3 text-sm"
            style={{
              background: resetError ? "var(--accent-coral-muted)" : "var(--accent-primary-muted)",
              color: resetError ? "var(--accent-coral)" : "var(--accent-primary)",
              border: resetError ? "1px solid rgba(232, 76, 94, 0.22)" : "1px solid rgba(0, 188, 163, 0.22)",
            }}
          >
            {resetError || resetResult}
          </div>
        )}
      </form>

      {/* Channels */}
      <div className="space-y-4">
        <h2
          className="font-display text-xl font-bold flex items-center gap-2"
          style={{ color: "var(--text-primary)" }}
        >
          Canais de Comunicação
          <Badge variant="neutral">{canais.length} cadastrados</Badge>
        </h2>

        {loadError && (
          <div
            className="rounded-lg px-4 py-3 text-sm"
            style={{
              background: "var(--accent-coral-muted)",
              color: "var(--accent-coral)",
              border: "1px solid rgba(232, 76, 94, 0.22)",
            }}
          >
            {loadError}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw
              className="h-6 w-6 animate-spin"
              style={{ color: "var(--accent-primary)" }}
            />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {canais.map((canal) => (
              <div
                key={canal.id}
                className="relative glass-card p-6 transition-all"
                style={{
                  borderColor: canal.ativo
                    ? "rgba(16, 185, 129, 0.3)"
                    : undefined,
                  boxShadow: canal.ativo
                    ? "var(--shadow-glow-teal)"
                    : undefined,
                }}
              >
                {/* Active Badge */}
                {canal.ativo && (
                  <div className="absolute top-4 right-4">
                    <Badge
                      variant="success"
                      icon={<CheckCircle2 className="h-3.5 w-3.5" />}
                    >
                      CANAL ATIVO
                    </Badge>
                  </div>
                )}

                <div className="flex items-start gap-4">
                  <div
                    className="flex h-12 w-12 items-center justify-center rounded-2xl"
                    style={{
                      background:
                        canal.provider === "UAZAPI"
                          ? "var(--accent-amber-muted)"
                          : "var(--accent-blue-muted)",
                    }}
                  >
                    {canal.provider.toLowerCase() === "uazapi" ? (
                      <QrCode
                        className="h-6 w-6"
                        style={{ color: "var(--accent-amber)" }}
                      />
                    ) : (
                      <Smartphone
                        className="h-6 w-6"
                        style={{ color: "var(--accent-blue)" }}
                      />
                    )}
                  </div>

                  <div className="space-y-2 flex-1 pr-16">
                    <div>
                      <span
                        className="text-[10px] font-bold uppercase tracking-wider"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {canal.provider.toLowerCase() === "uazapi"
                          ? "Canal Não Oficial (UAZAPI)"
                          : "Oficial (Meta Cloud API)"}
                      </span>
                      <h3
                        className="font-display text-lg font-bold leading-snug"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {canal.nome}
                      </h3>
                    </div>

                    {/* Connection Status */}
                    <div className="flex items-center gap-3 text-xs">
                      <span
                        className="flex items-center gap-1.5"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        <span
                          className={`h-2.5 w-2.5 rounded-full ${
                            canal.status === "conectado" ? "animate-pulse" : ""
                          }`}
                          style={{
                            backgroundColor:
                              canal.status === "conectado"
                                ? "var(--accent-primary)"
                                : "var(--accent-coral)",
                          }}
                        />
                        <strong className="capitalize">{canal.status}</strong>
                      </span>

                      {canal.qualidade && (
                        <Badge variant="success">
                          Qualidade: {canal.qualidade}
                        </Badge>
                      )}
                    </div>

                    <div className="grid grid-cols-1 gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                      <span className="flex items-center gap-1.5">
                        <Phone className="h-3.5 w-3.5" style={{ color: "var(--accent-blue)" }} />
                        {formatPhone(canal.telefone)}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Clock3 className="h-3.5 w-3.5" style={{ color: "var(--accent-amber)" }} />
                        Verificado em {formatLastCheck(canal.ultimo_healthcheck_em)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Capabilities */}
                <div
                  className="mt-5 pt-4 grid grid-cols-2 gap-2 text-xs"
                  style={{
                    borderTop: "1px solid var(--line)",
                    color: "var(--text-secondary)",
                  }}
                >
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck
                      className="h-3.5 w-3.5"
                      style={{ color: "var(--accent-primary)" }}
                    />
                    <span>
                      Janela 24h:{" "}
                      <strong>
                        {canal.provider.toLowerCase() === "meta" ? "Sim" : "Não"}
                      </strong>
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Zap
                      className="h-3.5 w-3.5"
                      style={{ color: "var(--accent-amber)" }}
                    />
                    <span>
                      Anti-ban Delay:{" "}
                      <strong>
                        {canal.provider.toLowerCase() === "uazapi" ? "Sim (1-3s)" : "N/A"}
                      </strong>
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-5 flex items-center justify-between pt-2">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setEditingChannel(canal)}
                      className="glass-btn glass-btn-ghost text-xs"
                      title="Editar instância"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      Editar
                    </button>
                    <button
                      onClick={() => setDeletingChannel(canal)}
                      className="glass-btn glass-btn-ghost text-xs"
                      title="Excluir instância"
                      style={{ color: "var(--accent-coral)" }}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Excluir
                    </button>
                  </div>

                  {canal.provider.toLowerCase() === "uazapi" &&
                    canal.status !== "conectado" && (
                      <button
                        onClick={() => setModalOpen(true)}
                        className="text-xs font-semibold hover:underline flex items-center gap-1"
                        style={{ color: "var(--accent-primary)" }}
                      >
                        <QrCode className="h-3.5 w-3.5" />
                        Re-gerar QR Code
                      </button>
                    )}

                  {!canal.ativo ? (
                    <button
                      onClick={() => handleToggleAtivo(canal)}
                      className="glass-btn glass-btn-ghost ml-auto text-xs"
                      style={{
                        borderColor: "rgba(16, 185, 129, 0.3)",
                        color: "var(--accent-primary)",
                      }}
                    >
                      Ativar este Canal
                    </button>
                  ) : (
                    <span
                      className="ml-auto text-xs italic"
                      style={{ color: "var(--text-muted)" }}
                    >
                      Em operação
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Horário de Funcionamento */}
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <h2
            className="font-display text-xl font-bold flex items-center gap-2"
            style={{ color: "var(--text-primary)" }}
          >
            Horário de Funcionamento
            <Badge variant="neutral">{turnos.length} turnos cadastrados</Badge>
          </h2>
          <button onClick={abrirModalCriarTurno} className="glass-btn glass-btn-primary text-xs" disabled={!tenantId}>
            <Plus className="h-4 w-4" />
            <span>Novo Turno</span>
          </button>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          Usado pela IA para nunca oferecer horário de prova/retirada fora do expediente real da loja.
          Alterações valem imediatamente, sem precisar de deploy.
        </p>

        {erroTurnos && (
          <div
            className="rounded-lg px-4 py-3 text-sm"
            style={{
              background: "var(--accent-coral-muted)",
              color: "var(--accent-coral)",
              border: "1px solid rgba(232, 76, 94, 0.22)",
            }}
          >
            {erroTurnos}
          </div>
        )}

        {carregandoTurnos ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-6 w-6 animate-spin" style={{ color: "var(--accent-primary)" }} />
          </div>
        ) : (
          <div className="glass-card divide-y" style={{ borderColor: "var(--line)" }}>
            {DIAS_SEMANA.map((nomeDia, diaSemana) => (
              <div key={diaSemana} className="flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-2 sm:w-40 shrink-0">
                  <CalendarClock className="h-4 w-4" style={{ color: "var(--accent-primary)" }} />
                  <span className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
                    {nomeDia}
                  </span>
                </div>
                <div className="flex flex-1 flex-wrap items-center gap-2">
                  {(turnosPorDia[diaSemana] || []).length === 0 ? (
                    <span className="text-xs italic" style={{ color: "var(--text-muted)" }}>
                      Fechado
                    </span>
                  ) : (
                    turnosPorDia[diaSemana].map((t) => (
                      <span
                        key={t.id}
                        className="inline-flex items-center gap-2 rounded-md px-2.5 py-1 text-xs font-medium"
                        style={{ background: "var(--c2)", color: "var(--text-secondary)" }}
                      >
                        {hhmm(t.hora_abertura)}–{hhmm(t.hora_fechamento)}
                        <button
                          onClick={() => abrirModalEditarTurno(t)}
                          title="Editar turno"
                          style={{ color: "var(--accent-primary)" }}
                        >
                          <Pencil className="h-3 w-3" />
                        </button>
                        <button
                          onClick={() => setTurnoExcluindo(t)}
                          title="Excluir turno"
                          style={{ color: "var(--accent-coral)" }}
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </span>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal Criar/Editar Turno */}
      {modalTurnoAberto && (
        <div className="modal-overlay">
          <form onSubmit={handleSubmitTurno} className="modal-content w-full max-w-md p-6 space-y-4">
            <div className="flex items-center gap-3">
              <CalendarClock className="h-5 w-5 shrink-0" style={{ color: "var(--accent-primary)" }} />
              <h3 className="font-display text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                {turnoEditando ? "Editar Turno" : "Novo Turno"}
              </h3>
            </div>

            <div className="space-y-3">
              <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                Dia da semana
                <select
                  name="dia_semana"
                  defaultValue={turnoEditando?.dia_semana ?? 1}
                  className="glass-select mt-1.5"
                  required
                >
                  {DIAS_SEMANA.map((nome, idx) => (
                    <option key={idx} value={idx}>
                      {nome}
                    </option>
                  ))}
                </select>
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                  Abertura
                  <input
                    type="time"
                    name="hora_abertura"
                    defaultValue={turnoEditando ? hhmm(turnoEditando.hora_abertura) : ""}
                    required
                    className="glass-input mt-1.5"
                  />
                </label>
                <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                  Fechamento
                  <input
                    type="time"
                    name="hora_fechamento"
                    defaultValue={turnoEditando ? hhmm(turnoEditando.hora_fechamento) : ""}
                    required
                    className="glass-input mt-1.5"
                  />
                </label>
              </div>
            </div>

            {erroFormTurno && (
              <div
                className="rounded-lg px-3 py-2 text-xs"
                style={{ background: "var(--accent-coral-muted)", color: "var(--accent-coral)" }}
              >
                {erroFormTurno}
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2" style={{ borderTop: "1px solid var(--line)" }}>
              <button
                type="button"
                onClick={() => {
                  setModalTurnoAberto(false);
                  setTurnoEditando(null);
                }}
                className="glass-btn glass-btn-ghost text-xs"
              >
                Cancelar
              </button>
              <button type="submit" disabled={salvandoTurno} className="glass-btn glass-btn-primary text-xs">
                {salvandoTurno ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Aviso de sobreposição de turnos (AC 6) */}
      {avisoSobreposicao && (
        <div className="modal-overlay">
          <div className="modal-content w-full max-w-md p-6 space-y-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-6 w-6 shrink-0" style={{ color: "var(--accent-amber)" }} />
              <h3 className="font-display text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                Turnos se sobrepõem
              </h3>
            </div>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              O turno {hhmm(avisoSobreposicao.hora_abertura)}–{hhmm(avisoSobreposicao.hora_fechamento)} em{" "}
              <strong>{DIAS_SEMANA[avisoSobreposicao.dia_semana]}</strong> se sobrepõe a outro turno já cadastrado
              nesse dia. Isso não é bloqueado pelo sistema, mas normalmente é engano no cadastro. Deseja salvar
              mesmo assim?
            </p>
            <div className="flex justify-end gap-3 pt-2" style={{ borderTop: "1px solid var(--line)" }}>
              <button onClick={() => setAvisoSobreposicao(null)} className="glass-btn glass-btn-ghost text-xs">
                Cancelar
              </button>
              <button
                onClick={() => void salvarTurno(avisoSobreposicao)}
                disabled={salvandoTurno}
                className="glass-btn glass-btn-primary text-xs"
              >
                {salvandoTurno ? "Salvando..." : "Salvar mesmo assim"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Excluir Turno */}
      {turnoExcluindo && (
        <div className="modal-overlay">
          <div className="modal-content w-full max-w-md p-6 space-y-4">
            <div className="flex items-center gap-3">
              <Trash2 className="h-5 w-5 shrink-0" style={{ color: "var(--accent-coral)" }} />
              <h3 className="font-display text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                Excluir Turno
              </h3>
            </div>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Remover o turno {hhmm(turnoExcluindo.hora_abertura)}–{hhmm(turnoExcluindo.hora_fechamento)} de{" "}
              <strong>{DIAS_SEMANA[turnoExcluindo.dia_semana]}</strong>? A IA deixará de oferecer esse intervalo em
              agendamentos imediatamente.
            </p>
            <div className="flex justify-end gap-3 pt-2" style={{ borderTop: "1px solid var(--line)" }}>
              <button onClick={() => setTurnoExcluindo(null)} className="glass-btn glass-btn-ghost text-xs">
                Cancelar
              </button>
              <button
                onClick={confirmarExcluirTurno}
                disabled={salvandoTurno}
                className="glass-btn glass-btn-primary text-xs"
                style={{ background: "var(--accent-coral)" }}
              >
                {salvandoTurno ? "Excluindo..." : "Excluir"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmingChannel && (
        <div className="modal-overlay">
          <div className="modal-content w-full max-w-md p-6 space-y-4">
            <div className="flex items-center gap-3">
              <AlertTriangle
                className="h-6 w-6 shrink-0"
                style={{ color: "var(--accent-amber)" }}
              />
              <h3
                className="font-display text-lg font-bold"
                style={{ color: "var(--text-primary)" }}
              >
                Confirmar Troca de Canal
              </h3>
            </div>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Deseja ativar o canal{" "}
              <strong>{confirmingChannel.nome}</strong>? O canal atualmente
              ativo será desativado. A mudança passa a valer a partir da
              próxima mensagem processada.
            </p>
            <div
              className="flex justify-end gap-3 pt-2"
              style={{ borderTop: "1px solid var(--line)" }}
            >
              <button
                onClick={() => setConfirmingChannel(null)}
                className="glass-btn glass-btn-ghost text-xs"
              >
                Cancelar
              </button>
              <button
                onClick={confirmSwitchChannel}
                className="glass-btn glass-btn-primary text-xs"
              >
                Sim, Ativar Canal
              </button>
            </div>
          </div>
        </div>
      )}

      {editingChannel && (
        <div className="modal-overlay">
          <form onSubmit={handleSalvarEdicao} className="modal-content w-full max-w-md p-6 space-y-4">
            <div className="flex items-center gap-3">
              <Pencil
                className="h-5 w-5 shrink-0"
                style={{ color: "var(--accent-primary)" }}
              />
              <h3
                className="font-display text-lg font-bold"
                style={{ color: "var(--text-primary)" }}
              >
                Editar Instância
              </h3>
            </div>

            <div className="space-y-3">
              <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                Nome
                <input
                  name="nome"
                  defaultValue={editingChannel.nome}
                  required
                  className="glass-input mt-1.5"
                />
              </label>
              <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                Telefone
                <input
                  name="telefone"
                  defaultValue={editingChannel.telefone || ""}
                  placeholder="5585988124477"
                  className="glass-input mt-1.5"
                />
              </label>
            </div>

            <div className="flex justify-end gap-3 pt-2" style={{ borderTop: "1px solid var(--line)" }}>
              <button
                type="button"
                onClick={() => setEditingChannel(null)}
                className="glass-btn glass-btn-ghost text-xs"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={saving}
                className="glass-btn glass-btn-primary text-xs"
              >
                {saving ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </form>
        </div>
      )}

      {deletingChannel && (
        <div className="modal-overlay">
          <div className="modal-content w-full max-w-md p-6 space-y-4">
            <div className="flex items-center gap-3">
              <Trash2
                className="h-5 w-5 shrink-0"
                style={{ color: "var(--accent-coral)" }}
              />
              <h3
                className="font-display text-lg font-bold"
                style={{ color: "var(--text-primary)" }}
              >
                Excluir Instância
              </h3>
            </div>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Deseja remover <strong>{deletingChannel.nome}</strong> da lista de
              canais? Ela será desativada e não aparecerá mais em configurações.
            </p>
            <div className="flex justify-end gap-3 pt-2" style={{ borderTop: "1px solid var(--line)" }}>
              <button
                onClick={() => setDeletingChannel(null)}
                className="glass-btn glass-btn-ghost text-xs"
              >
                Cancelar
              </button>
              <button
                onClick={confirmDeleteChannel}
                disabled={saving}
                className="glass-btn glass-btn-primary text-xs"
                style={{ background: "var(--accent-coral)" }}
              >
                {saving ? "Excluindo..." : "Excluir"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* QR Code Modal */}
      <UazapiQrModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={() => fetchCanais()}
      />
    </div>
  );
}
