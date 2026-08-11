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
    <div className="space-[#1F1B17] space-y-8 p-6 max-w-6xl mx-auto">
      {/* Cabeçalho da Seção */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#E7DFD2]">
        <div>
          <h1 className="font-serif text-3xl font-bold text-[#072F53]">Configurações da Conta</h1>
          <p className="mt-1 text-sm text-[#6B5E52]">
            Gestão de Canais de Comunicação, Automações e Parâmetros Operacionais do ALFAIA.
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-[#0E4A7B] px-5 py-2.5 text-sm font-medium text-white shadow-md hover:bg-[#072F53] transition-all"
        >
          <Plus className="h-4 w-4 text-[#EBB832]" />
          <span>Nova Instância UAZAPI (QR Code)</span>
        </button>
      </div>

      {/* Alerta de Canal Ativo / Regra de Negócio */}
      <div className="rounded-2xl border border-[#E7DFD2] bg-[#FAF7F2] p-5 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#0E4A7B] text-[#EBB832]">
            <Radio className="h-5 w-5" />
          </div>
          <div className="space-y-1">
            <h3 className="font-serif text-lg font-bold text-[#072F53]">Regra de Seleção de Canal</h3>
            <p className="text-xs text-[#6B5E52] leading-relaxed">
              Conforme PRD §14.3 (AC 14.7), exatamente <strong>um canal</strong> pode estar ativo por tenant de cada vez.
              A troca de canal vale a partir da <strong>próxima mensagem processada</strong> e todo o histórico é mantido intacto.
            </p>
          </div>
        </div>
      </div>

      {/* Lista de Canais Configurados */}
      <div className="space-y-4">
        <h2 className="font-serif text-xl font-bold text-[#072F53] flex items-center gap-2">
          <span>Canais de Comunicação</span>
          <span className="text-xs font-sans font-normal text-[#6B5E52] bg-[#F3F6F9] px-2.5 py-0.5 rounded-full border border-[#E7DFD2]">
            {canais.length} cadastrados
          </span>
        </h2>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-6 w-6 animate-spin text-[#0E4A7B]" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {canais.map((canal) => (
              <div
                key={canal.id}
                className={`relative rounded-2xl border bg-white p-6 shadow-sm transition-all hover:shadow-md ${
                  canal.ativo ? "border-[#A67C2E] ring-1 ring-[#A67C2E]" : "border-[#E7DFD2]"
                }`}
              >
                {/* Badge Ativo */}
                {canal.ativo && (
                  <div className="absolute top-4 right-4 flex items-center gap-1.5 rounded-full bg-[#0E4A7B] px-3 py-1 text-xs font-semibold text-white shadow-sm">
                    <CheckCircle2 className="h-3.5 w-3.5 text-[#EBB832]" />
                    <span>CANAL ATIVO</span>
                  </div>
                )}

                <div className="flex items-start gap-4">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${
                    canal.provider === "UAZAPI" ? "bg-amber-50 text-[#A67C2E]" : "bg-blue-50 text-[#0E4A7B]"
                  }`}>
                    {canal.provider === "UAZAPI" ? <QrCode className="h-6 w-6" /> : <Smartphone className="h-6 w-6" />}
                  </div>

                  <div className="space-y-2 flex-1 pr-16">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#6B5E52]">
                        {canal.provider === "UAZAPI" ? "Canal Não Oficial (UAZAPI)" : "Oficial (Meta Cloud API)"}
                      </span>
                      <h3 className="font-serif text-lg font-bold text-[#072F53] leading-snug">{canal.nome}</h3>
                    </div>

                    {/* Status de Conexão */}
                    <div className="flex items-center gap-3 text-xs">
                      <span className="flex items-center gap-1.5 text-[#6B5E52]">
                        <span className={`h-2.5 w-2.5 rounded-full ${
                          canal.status === "conectado" ? "bg-emerald-500 animate-pulse" : "bg-red-400"
                        }`} />
                        <strong className="capitalize">{canal.status}</strong>
                      </span>

                      {canal.qualidade && (
                        <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                          Qualidade: {canal.qualidade}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Capabilities do Canal */}
                <div className="mt-5 border-t border-[#E7DFD2] pt-4 grid grid-cols-2 gap-2 text-xs text-[#6B5E52]">
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck className="h-3.5 w-3.5 text-[#0E4A7B]" />
                    <span>Janela 24h: <strong>{canal.provider === "META" ? "Sim" : "Não"}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5 text-[#A67C2E]" />
                    <span>Anti-ban Delay: <strong>{canal.provider === "UAZAPI" ? "Sim (1-3s)" : "N/A"}</strong></span>
                  </div>
                </div>

                {/* Ações */}
                <div className="mt-5 flex items-center justify-between pt-2">
                  {canal.provider === "UAZAPI" && canal.status !== "conectado" && (
                    <button
                      onClick={() => setModalOpen(true)}
                      className="text-xs font-semibold text-[#0E4A7B] hover:underline flex items-center gap-1"
                    >
                      <QrCode className="h-3.5 w-3.5" />
                      <span>Re-gerar QR Code</span>
                    </button>
                  )}

                  {!canal.ativo ? (
                    <button
                      onClick={() => handleToggleAtivo(canal)}
                      className="ml-auto rounded-xl border border-[#0E4A7B] px-4 py-1.5 text-xs font-semibold text-[#0E4A7B] hover:bg-[#0E4A7B] hover:text-white transition-all"
                    >
                      Ativar este Canal
                    </button>
                  ) : (
                    <span className="ml-auto text-xs text-[#6B5E52] italic">Em operação</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal de Confirmação de Troca de Canal */}
      {confirmingChannel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-[#E7DFD2] space-y-4">
            <div className="flex items-center gap-3 text-amber-600">
              <AlertTriangle className="h-6 w-6 shrink-0" />
              <h3 className="font-serif text-lg font-bold text-[#072F53]">Confirmar Troca de Canal</h3>
            </div>
            <p className="text-sm text-[#6B5E52]">
              Deseja ativar o canal <strong>{confirmingChannel.nome}</strong>? O canal atualmente ativo será desativado.
              A mudança passa a valer a partir da próxima mensagem processada.
            </p>
            <div className="flex justify-end gap-3 pt-2 border-t border-[#E7DFD2]">
              <button
                onClick={() => setConfirmingChannel(null)}
                className="rounded-xl border border-[#E7DFD2] px-4 py-2 text-xs font-medium text-[#1F1B17]"
              >
                Cancelar
              </button>
              <button
                onClick={confirmSwitchChannel}
                className="rounded-xl bg-[#0E4A7B] px-4 py-2 text-xs font-semibold text-white shadow hover:bg-[#072F53]"
              >
                Sim, Ativar Canal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal QR Code UAZAPI */}
      <UazapiQrModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={() => fetchCanais()}
      />
    </div>
  );
}
