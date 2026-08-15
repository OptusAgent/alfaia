"use client";

import { useState } from "react";
import { Send, AlertTriangle, CheckCircle, X, ShieldAlert } from "lucide-react";

export interface MensagemTemplate {
  id: string;
  nome: string;
  corpo: string;
  templateMeta?: string | null;
}

interface FollowupDispatchModalProps {
  isOpen: boolean;
  onClose: () => void;
  leadId: string;
  nomeLead: string;
  canalAtivo: "uazapi" | "meta";
  janelaMetaAberta: boolean;
  userRole: "dono" | "atendente" | "operador";
  onDisparado?: () => void;
}

const TEMPLATES_PADRAO: MensagemTemplate[] = [
  {
    id: "msg_1",
    nome: "Lembrete Prova Vestido",
    corpo: "Olá! Gostaria de confirmar nossa data agendada para prova do seu vestido?",
    templateMeta: "template_lembrete_prova",
  },
  {
    id: "msg_2",
    nome: "Segunda Chamada Simples",
    corpo: "Passando para saber se você ainda tem interesse nos modelos que enviamos!",
    templateMeta: null,
  },
];

export default function FollowupDispatchModal({
  isOpen,
  onClose,
  leadId,
  nomeLead,
  canalAtivo,
  janelaMetaAberta,
  userRole,
  onDisparado,
}: FollowupDispatchModalProps) {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("msg_1");
  const [isSending, setIsSending] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  if (!isOpen) return null;

  const isOperadorBlocked = userRole === "operador";
  const selectedTemplate = TEMPLATES_PADRAO.find((t) => t.id === selectedTemplateId);
  const isMetaWindowClosed = canalAtivo === "meta" && !janelaMetaAberta;
  const isTemplateInvalidForMeta = isMetaWindowClosed && selectedTemplate && !selectedTemplate.templateMeta;

  const handleDisparar = async () => {
    if (isOperadorBlocked) {
      setErro("Permissão negada. Apenas 'dono' ou 'atendente' podem disparar follow-ups.");
      return;
    }
    if (isTemplateInvalidForMeta) {
      setErro("Janela Meta fechada: esta mensagem não possui template aprovado pela Meta.");
      return;
    }

    setIsSending(true);
    setErro(null);

    try {
      // Simulação do envio POST /api/leads/{id}/followup
      setTimeout(() => {
        setIsSending(false);
        if (onDisparado) onDisparado();
        onClose();
      }, 600);
    } catch (e: any) {
      setIsSending(false);
      setErro(e.message || "Erro ao disparar follow-up.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-neutral-900/50 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-neutral-200 space-y-5 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
          <div>
            <h3 className="text-lg font-bold text-neutral-900 flex items-center gap-2">
              <Send className="h-5 w-5 text-brand-600" />
              Disparar Follow-up Manual
            </h3>
            <p className="text-xs text-neutral-500">Lead: <strong>{nomeLead}</strong></p>
          </div>
          <button onClick={onClose} className="rounded-md p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Warning de Permissão (AC 3, PRD §4.2) */}
        {isOperadorBlocked && (
          <div className="flex items-start gap-2.5 rounded-lg bg-rose-50 p-3 border border-rose-200 text-rose-800 text-xs">
            <ShieldAlert className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <strong>Acesso Restrito:</strong> Seu perfil (operador) não possui permissão para disparar mensagens de follow-up. Esta ação é exclusiva para <u>Dono</u> e <u>Atendente</u>.
            </div>
          </div>
        )}

        {/* Warning de Janela 24h Meta (AC 2, AC 10.6) */}
        {isMetaWindowClosed && (
          <div className="flex items-start gap-2.5 rounded-lg bg-amber-50 p-3 border border-amber-200 text-amber-900 text-xs">
            <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <strong>Janela Meta de 24h Fechada:</strong> Apenas mensagens com template HSM pré-aprovado pela Meta podem ser enviadas para este lead.
            </div>
          </div>
        )}

        {/* Lista de Mensagens Pré-cadastradas (AC 1) */}
        <div className="space-y-3">
          <label className="text-xs font-semibold text-neutral-700">Selecione a mensagem pré-cadastrada:</label>
          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {TEMPLATES_PADRAO.map((tpl) => {
              const isInvalid = isMetaWindowClosed && !tpl.templateMeta;

              return (
                <div
                  key={tpl.id}
                  onClick={() => !isInvalid && setSelectedTemplateId(tpl.id)}
                  className={`flex flex-col gap-1.5 rounded-xl border p-3 cursor-pointer transition ${
                    selectedTemplateId === tpl.id
                      ? "border-brand-500 bg-brand-50/40 ring-1 ring-brand-500"
                      : "border-neutral-200 hover:border-neutral-300 bg-white"
                  } ${isInvalid ? "opacity-50 cursor-not-allowed bg-neutral-50" : ""}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-neutral-900">{tpl.nome}</span>
                    {tpl.templateMeta ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                        <CheckCircle className="h-3 w-3" /> Template Meta
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
                        Texto Livre
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-neutral-600 line-clamp-2 italic">"{tpl.corpo}"</p>
                </div>
              );
            })}
          </div>
        </div>

        {erro && (
          <div className="text-xs font-semibold text-rose-600 bg-rose-50 p-2.5 rounded-lg border border-rose-200">
            {erro}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 border-t border-neutral-100 pt-3">
          <button
            onClick={onClose}
            className="rounded-lg border border-neutral-300 px-4 py-2 text-xs font-semibold text-neutral-700 hover:bg-neutral-100 transition"
          >
            Cancelar
          </button>
          <button
            onClick={handleDisparar}
            disabled={isSending || isOperadorBlocked || isTemplateInvalidForMeta}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-xs font-semibold text-white hover:bg-brand-700 transition disabled:opacity-50"
          >
            <Send className="h-3.5 w-3.5" />
            {isSending ? "Enviando..." : "Disparar 1-Clique"}
          </button>
        </div>
      </div>
    </div>
  );
}
