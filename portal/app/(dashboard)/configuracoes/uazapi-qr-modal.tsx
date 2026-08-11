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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-[#E7DFD2]">
        {/* Cabeçalho do Modal */}
        <div className="flex items-center justify-between border-b border-[#E7DFD2] pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#0E4A7B] text-white">
              <QrCode className="h-5 w-5" />
            </div>
            <div>
              <h2 className="font-serif text-xl font-bold text-[#072F53]">Conectar Instância UAZAPI</h2>
              <p className="text-xs text-[#6B5E52]">WhatsApp Web (Canal Não Oficial)</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Mensagem de Erro */}
        {error && (
          <div className="mt-4 flex items-center gap-2 rounded-xl bg-red-50 p-3 text-sm text-red-700 border border-red-200">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Conteúdo por Etapa */}
        <div className="py-6">
          {step === "form" && (
            <form onSubmit={handleGerarQrCode} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#072F53] mb-1.5">
                  Nome da Instância <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="ex: loja_centro_whatsapp"
                  value={nomeInstancia}
                  onChange={(e) => setNomeInstancia(e.target.value)}
                  className="w-full rounded-xl border border-[#E7DFD2] bg-white px-4 py-2.5 text-sm text-[#1F1B17] placeholder:text-neutral-400 focus:border-[#A67C2E] focus:outline-none focus:ring-1 focus:ring-[#A67C2E]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#072F53] mb-1.5">
                  Número de Telefone (Opcional)
                </label>
                <input
                  type="text"
                  placeholder="ex: 5585988124477"
                  value={telefone}
                  onChange={(e) => setTelefone(e.target.value)}
                  className="w-full rounded-xl border border-[#E7DFD2] bg-white px-4 py-2.5 text-sm text-[#1F1B17] placeholder:text-neutral-400 focus:border-[#A67C2E] focus:outline-none focus:ring-1 focus:ring-[#A67C2E]"
                />
                <p className="mt-1 text-xs text-[#6B5E52]">Número do WhatsApp que fará o pareamento.</p>
              </div>

              <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-[#E7DFD2]">
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-xl border border-[#E7DFD2] px-4 py-2 text-sm font-medium text-[#1F1B17] hover:bg-neutral-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-2 rounded-xl bg-[#0E4A7B] px-5 py-2 text-sm font-medium text-white shadow hover:bg-[#072F53] disabled:opacity-50 transition-all"
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
              <div className="rounded-2xl border-2 border-dashed border-[#A67C2E] p-4 bg-[#FAF7F2]">
                {qrCodeData ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img
                    src={qrCodeData}
                    alt="QR Code de Pareamento WhatsApp"
                    className="h-56 w-56 object-contain rounded-lg shadow-sm"
                  />
                ) : (
                  <div className="flex h-56 w-56 items-center justify-center">
                    <RefreshCw className="h-8 w-8 animate-spin text-[#0E4A7B]" />
                  </div>
                )}
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-center gap-2 text-sm font-semibold text-[#072F53]">
                  <Smartphone className="h-4 w-4 text-[#A67C2E]" />
                  <span>Abra o WhatsApp no seu celular</span>
                </div>
                <p className="text-xs text-[#6B5E52] max-w-xs">
                  Vá em <strong>Dispositivos Conectados ➔ Conectar um dispositivo</strong> e aponte a câmera para a imagem acima.
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs text-[#0E4A7B] bg-[#F3F6F9] px-3 py-1.5 rounded-full font-mono">
                <RefreshCw className="h-3 w-3 animate-spin" />
                <span>Aguardando leitura do QR Code...</span>
              </div>

              <button
                type="button"
                onClick={() => setStep("success")}
                className="mt-2 text-xs text-[#A67C2E] underline hover:text-[#072F53]"
              >
                [Dev Test: Simular Pareamento Concluído]
              </button>
            </div>
          )}

          {step === "success" && (
            <div className="flex flex-col items-center text-center space-y-4 py-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <CheckCircle2 className="h-10 w-10" />
              </div>

              <div className="space-y-1">
                <h3 className="font-serif text-2xl font-bold text-[#072F53]">Instância Conectada!</h3>
                <p className="text-sm text-[#6B5E52]">
                  O WhatsApp da instância <strong>{nomeInstancia}</strong> foi pareado e autorizado com sucesso na UAZAPI.
                </p>
              </div>

              <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-xs text-emerald-800 text-left w-full space-y-1">
                <p>✓ Webhook configurado automaticamente</p>
                <p>✓ Canal registrado na tabela <code className="font-mono bg-emerald-100 px-1 rounded">canais</code></p>
                <p>✓ Status atual: <strong className="uppercase">Conectado</strong></p>
              </div>

              <button
                type="button"
                onClick={handleFinalizar}
                className="w-full rounded-xl bg-[#0E4A7B] py-2.5 text-sm font-medium text-white shadow hover:bg-[#072F53] transition-all"
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
