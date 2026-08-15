"use client";

import { useState, useEffect } from "react";
import { QrCode, Smartphone, CheckCircle2, RefreshCw, X, AlertCircle } from "lucide-react";

interface UazapiQrModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function UazapiQrModal({ isOpen, onClose, onSuccess }: UazapiQrModalProps) {
  const [step, setStep] = useState<"form" | "qrcode" | "success">("form");
  const [nomeInstancia, setNomeInstancia] = useState("");
  const [telefone, setTelefone] = useState("");
  const [qrCodeData, setQrCodeData] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Polling de status quando está exibindo o QR Code (Hook deve ser chamado incondicionalmente)
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isOpen && step === "qrcode") {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`/api/canais/uazapi/connect?instancia=${encodeURIComponent(nomeInstancia)}`);
          const data = await res.json();
          if (data.status === "conectado") {
            setStep("success");
            clearInterval(interval);
          }
        } catch {
          // ignora erro transitório no polling
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [isOpen, step, nomeInstancia]);

  if (!isOpen) return null;

  async function handleGerarQrCode(e: React.FormEvent) {
    e.preventDefault();
    if (!nomeInstancia.trim()) {
      setError("O nome da instância é obrigatório.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const response = await fetch("/api/canais/uazapi/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome: nomeInstancia, telefone }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Erro ao conectar com UAZAPI");
      }

      setQrCodeData(data.qrcode || "data:image/png;base64,iVBORw0KGgoAAAANSU5EUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==");
      setStep("qrcode");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao gerar QR Code";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  function handleFinalizar() {
    onSuccess();
    onClose();
    // Reseta o estado do modal
    setStep("form");
    setNomeInstancia("");
    setTelefone("");
    setQrCodeData(null);
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content w-full max-w-lg p-6">
        {/* Header */}
        <div
          className="flex items-center justify-between pb-4"
          style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.06)" }}
        >
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl"
              style={{ background: "var(--accent-primary-muted)" }}
            >
              <QrCode className="h-5 w-5" style={{ color: "var(--accent-primary)" }} />
            </div>
            <div>
              <h2
                className="font-display text-xl font-bold"
                style={{ color: "var(--text-primary)" }}
              >
                Conectar Instância UAZAPI
              </h2>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                WhatsApp Web (Canal Não Oficial)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 transition-colors"
            style={{ color: "var(--text-muted)" }}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Error */}
        {error && (
          <div
            className="mt-4 flex items-center gap-2 rounded-xl p-3 text-sm"
            style={{
              background: "var(--accent-coral-muted)",
              color: "var(--accent-coral)",
              border: "1px solid rgba(232, 76, 94, 0.2)",
            }}
          >
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Content by Step */}
        <div className="py-6">
          {step === "form" && (
            <form onSubmit={handleGerarQrCode} className="space-y-4">
              <div>
                <label
                  className="block text-xs font-semibold uppercase tracking-wider mb-1.5"
                  style={{ color: "var(--text-muted)" }}
                >
                  Nome da Instância <span style={{ color: "var(--accent-coral)" }}>*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="ex: loja_centro_whatsapp"
                  value={nomeInstancia}
                  onChange={(e) => setNomeInstancia(e.target.value)}
                  className="glass-input"
                />
              </div>

              <div>
                <label
                  className="block text-xs font-semibold uppercase tracking-wider mb-1.5"
                  style={{ color: "var(--text-muted)" }}
                >
                  Número de Telefone (Opcional)
                </label>
                <input
                  type="text"
                  placeholder="ex: 5585988124477"
                  value={telefone}
                  onChange={(e) => setTelefone(e.target.value)}
                  className="glass-input"
                />
                <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                  Número do WhatsApp que fará o pareamento.
                </p>
              </div>

              <div
                className="mt-6 flex justify-end gap-3 pt-4"
                style={{ borderTop: "1px solid rgba(255, 255, 255, 0.06)" }}
              >
                <button
                  type="button"
                  onClick={onClose}
                  className="glass-btn glass-btn-ghost text-sm"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="glass-btn glass-btn-primary text-sm"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>Gerando...</span>
                    </>
                  ) : (
                    <>
                      <QrCode className="h-4 w-4" />
                      <span>Gerar QR Code</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {step === "qrcode" && (
            <div className="flex flex-col items-center text-center space-y-4">
              <div
                className="rounded-2xl border-2 border-dashed p-3 bg-white"
                style={{
                  borderColor: "var(--accent-primary)",
                }}
              >
                {qrCodeData ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img
                    src={qrCodeData}
                    alt="QR Code de Pareamento WhatsApp"
                    className="h-56 w-56 object-contain rounded-lg"
                  />
                ) : (
                  <div className="flex h-56 w-56 items-center justify-center bg-white">
                    <RefreshCw
                      className="h-8 w-8 animate-spin"
                      style={{ color: "var(--accent-primary)" }}
                    />
                  </div>
                )}
              </div>

              <div className="space-y-1">
                <div
                  className="flex items-center justify-center gap-2 text-sm font-semibold"
                  style={{ color: "var(--text-primary)" }}
                >
                  <Smartphone className="h-4 w-4" style={{ color: "var(--accent-primary)" }} />
                  <span>Abra o WhatsApp no seu celular</span>
                </div>
                <p className="text-xs max-w-xs" style={{ color: "var(--text-secondary)" }}>
                  Vá em <strong>Dispositivos Conectados → Conectar um dispositivo</strong> e
                  aponte a câmera para a imagem acima.
                </p>
              </div>

              <div
                className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full font-mono"
                style={{
                  background: "var(--accent-primary-muted)",
                  color: "var(--accent-primary)",
                }}
              >
                <RefreshCw className="h-3 w-3 animate-spin" />
                <span>Aguardando leitura do QR Code...</span>
              </div>

              <button
                type="button"
                onClick={() => setStep("success")}
                className="mt-2 text-xs underline"
                style={{ color: "var(--text-muted)" }}
              >
                [Dev Test: Simular Pareamento Concluído]
              </button>
            </div>
          )}

          {step === "success" && (
            <div className="flex flex-col items-center text-center space-y-4 py-4">
              <div
                className="flex h-16 w-16 items-center justify-center rounded-full"
                style={{ background: "var(--accent-primary-muted)" }}
              >
                <CheckCircle2
                  className="h-10 w-10"
                  style={{ color: "var(--accent-primary)" }}
                />
              </div>

              <div className="space-y-1">
                <h3
                  className="font-display text-2xl font-bold"
                  style={{ color: "var(--text-primary)" }}
                >
                  Instância Conectada!
                </h3>
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  O WhatsApp da instância <strong>{nomeInstancia}</strong> foi
                  pareado e autorizado com sucesso na UAZAPI.
                </p>
              </div>

              <div
                className="rounded-xl p-3 text-xs text-left w-full space-y-1"
                style={{
                  background: "var(--accent-primary-muted)",
                  color: "var(--accent-primary)",
                  border: "1px solid rgba(16, 185, 129, 0.2)",
                }}
              >
                <p>✓ Webhook configurado automaticamente</p>
                <p>
                  ✓ Canal registrado na tabela{" "}
                  <code
                    className="font-mono px-1 rounded"
                    style={{ background: "rgba(16, 185, 129, 0.15)" }}
                  >
                    canais
                  </code>
                </p>
                <p>
                  ✓ Status atual: <strong className="uppercase">Conectado</strong>
                </p>
              </div>

              <button
                type="button"
                onClick={handleFinalizar}
                className="glass-btn glass-btn-primary w-full py-2.5 text-sm"
              >
                Concluir e Voltar
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
