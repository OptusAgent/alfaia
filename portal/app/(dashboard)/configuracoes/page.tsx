"use client";

import { useState, useEffect } from "react";
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
} from "lucide-react";
import { UazapiQrModal } from "./uazapi-qr-modal";
import { Badge } from "@/app/components/ui/Badge";

interface Canal {
  id: string;
  provider: string;
  nome: string;
  ativo: boolean;
  status: string;
  qualidade: string | null;
  uazapi_instancia: string | null;
}

export default function ConfiguracoesPage() {
  const [canais, setCanais] = useState<Canal[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmingChannel, setConfirmingChannel] = useState<Canal | null>(null);

  async function fetchCanais() {
    try {
      const res = await fetch("/api/canais");
      const data = await res.json();
      setCanais(data.canais || []);
    } catch {
      // fallback
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchCanais();
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

      {/* Channels */}
      <div className="space-y-4">
        <h2
          className="font-display text-xl font-bold flex items-center gap-2"
          style={{ color: "var(--text-primary)" }}
        >
          Canais de Comunicação
          <Badge variant="neutral">{canais.length} cadastrados</Badge>
        </h2>

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
                    {canal.provider === "UAZAPI" ? (
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
                        {canal.provider === "UAZAPI"
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
                        {canal.provider === "META" ? "Sim" : "Não"}
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
                        {canal.provider === "UAZAPI" ? "Sim (1-3s)" : "N/A"}
                      </strong>
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-5 flex items-center justify-between pt-2">
                  {canal.provider === "UAZAPI" &&
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

      {/* QR Code Modal */}
      <UazapiQrModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={() => fetchCanais()}
      />
    </div>
  );
}
