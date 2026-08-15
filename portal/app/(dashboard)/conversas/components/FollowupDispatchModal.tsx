"use client";

import { useState } from "react";
import { Badge } from "@/app/components/ui/Badge";
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
  leadId?: string;
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
    } catch (e: unknown) {
      setIsSending(false);
      const msg = e instanceof Error ? e.message : "Erro ao disparar follow-up.";
      setErro(msg);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content w-full max-w-lg p-6 space-y-5">
        {/* Header */}
        <div
          className="flex items-center justify-between pb-3"
          style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.06)" }}
        >
          <div>
            <h3
              className="text-lg font-bold font-display flex items-center gap-2"
              style={{ color: "var(--text-primary)" }}
            >
              <Send className="h-5 w-5" style={{ color: "var(--accent-primary)" }} />
              Disparar Follow-up Manual
            </h3>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              Lead: <strong>{nomeLead}</strong>
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1"
            style={{ color: "var(--text-muted)" }}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Permission Warning */}
        {isOperadorBlocked && (
          <div
            className="flex items-start gap-2.5 rounded-lg p-3 text-xs"
            style={{
              background: "var(--accent-coral-muted)",
              color: "var(--accent-coral)",
              border: "1px solid rgba(232, 76, 94, 0.2)",
            }}
          >
            <ShieldAlert className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <div>
              <strong>Acesso Restrito:</strong> Seu perfil (operador) não possui
              permissão para disparar mensagens de follow-up.
            </div>
          </div>
        )}

        {/* Meta Window Warning */}
        {isMetaWindowClosed && (
          <div
            className="flex items-start gap-2.5 rounded-lg p-3 text-xs"
            style={{
              background: "var(--accent-amber-muted)",
              color: "var(--accent-amber)",
              border: "1px solid var(--accent-amber-border)",
            }}
          >
            <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <div>
              <strong>Janela Meta de 24h Fechada:</strong> Apenas mensagens com
              template HSM pré-aprovado podem ser enviadas.
            </div>
          </div>
        )}

        {/* Template List */}
        <div className="space-y-3">
          <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
            Selecione a mensagem pré-cadastrada:
          </label>
          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {TEMPLATES_PADRAO.map((tpl) => {
              const isInvalid = isMetaWindowClosed && !tpl.templateMeta;

              return (
                <div
                  key={tpl.id}
                  onClick={() => !isInvalid && setSelectedTemplateId(tpl.id)}
                  className="flex flex-col gap-1.5 rounded-xl p-3 cursor-pointer transition-all"
                  style={{
                    background:
                      selectedTemplateId === tpl.id
                        ? "var(--accent-primary-muted)"
                        : "rgba(255, 255, 255, 0.04)",
                    border:
                      selectedTemplateId === tpl.id
                        ? "1px solid rgba(16, 185, 129, 0.3)"
                        : "1px solid rgba(255, 255, 255, 0.06)",
                    opacity: isInvalid ? 0.5 : 1,
                    cursor: isInvalid ? "not-allowed" : "pointer",
                  }}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className="text-xs font-bold"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {tpl.nome}
                    </span>
                    {tpl.templateMeta ? (
                      <Badge variant="success" icon={<CheckCircle className="h-3 w-3" />}>
                        Template Meta
                      </Badge>
                    ) : (
                      <Badge variant="neutral">Texto Livre</Badge>
                    )}
                  </div>
                  <p
                    className="text-xs line-clamp-2 italic"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    &quot;{tpl.corpo}&quot;
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {erro && (
          <div
            className="text-xs font-semibold p-2.5 rounded-lg"
            style={{
              background: "var(--accent-coral-muted)",
              color: "var(--accent-coral)",
              border: "1px solid rgba(232, 76, 94, 0.2)",
            }}
          >
            {erro}
          </div>
        )}

        {/* Actions */}
        <div
          className="flex items-center justify-end gap-3 pt-3"
          style={{ borderTop: "1px solid rgba(255, 255, 255, 0.06)" }}
        >
          <button onClick={onClose} className="glass-btn glass-btn-ghost text-xs">
            Cancelar
          </button>
          <button
            onClick={handleDisparar}
            disabled={isSending || isOperadorBlocked || !!isTemplateInvalidForMeta}
            className="glass-btn glass-btn-primary text-xs"
          >
            <Send className="h-3.5 w-3.5" />
            {isSending ? "Enviando..." : "Disparar 1-Clique"}
          </button>
        </div>
      </div>
    </div>
  );
}
