"use client";

import {
  UserPlus,
  ArrowRightLeft,
  Heart,
  Clock,
  Headphones,
  Calendar,
  Trash2,
  RotateCcw,
  AlertTriangle,
  FileText,
  Tag,
} from "lucide-react";

export interface EventoTimeline {
  id: string | number;
  tipo:
    | "lead_criado"
    | "status_mudou"
    | "interesse_alterado"
    | "followup_enviado"
    | "transbordo_aberto"
    | "transbordo_fechado"
    | "transbordo_assumido"
    | "transbordo_devolvido"
    | "agendou"
    | "descartado"
    | "reaberto"
    | "divergencia_ia_humano"
    | "nota";
  de?: string;
  para?: string;
  autor?: "ia" | "humano" | "sistema";
  motivo?: string;
  detalhe?: Record<string, any>;
  criado_em: string;
}

interface LeadTimelineProps {
  leadId: string;
  nomeLead: string;
  tags?: string[];
  eventos: EventoTimeline[];
}

export default function LeadTimeline({ leadId, nomeLead, tags = [], eventos }: LeadTimelineProps) {
  const renderIconeEvento = (tipo: EventoTimeline["tipo"]) => {
    switch (tipo) {
      case "lead_criado":
        return <UserPlus className="h-4 w-4 text-emerald-600" />;
      case "status_mudou":
        return <ArrowRightLeft className="h-4 w-4 text-blue-600" />;
      case "interesse_alterado":
        return <Heart className="h-4 w-4 text-pink-600" />;
      case "followup_enviado":
        return <Clock className="h-4 w-4 text-amber-600" />;
      case "transbordo_aberto":
      case "transbordo_fechado":
      case "transbordo_assumido":
      case "transbordo_devolvido":
        return <Headphones className="h-4 w-4 text-purple-600" />;
      case "agendou":
        return <Calendar className="h-4 w-4 text-teal-600" />;
      case "descartado":
        return <Trash2 className="h-4 w-4 text-rose-600" />;
      case "reaberto":
        return <RotateCcw className="h-4 w-4 text-cyan-600" />;
      case "divergencia_ia_humano":
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case "nota":
        return <FileText className="h-4 w-4 text-slate-600" />;
      default:
        return <Clock className="h-4 w-4 text-neutral-400" />;
    }
  };

  const renderConteudoEvento = (ev: EventoTimeline) => {
    switch (ev.tipo) {
      case "lead_criado":
        return (
          <div>
            <span className="font-semibold text-neutral-900">Lead criado no sistema</span>
            <p className="text-xs text-neutral-500">Primeiro contato registrado via automação.</p>
          </div>
        );
      case "status_mudou":
        return (
          <div>
            <span className="font-semibold text-neutral-900">Status alterado</span>:{" "}
            <span className="font-mono text-xs bg-neutral-100 px-1.5 py-0.5 rounded text-neutral-700">{ev.de}</span> &rarr;{" "}
            <span className="font-mono text-xs bg-brand-50 text-brand-800 font-bold px-1.5 py-0.5 rounded">{ev.para}</span>
            <span className="ml-2 text-[10px] uppercase font-bold text-neutral-400">({ev.autor})</span>
          </div>
        );
      case "interesse_alterado":
        return (
          <div>
            <span className="font-semibold text-neutral-900">Interesse/Evento atualizado</span>
            {ev.detalhe && (
              <div className="text-xs text-neutral-600 mt-0.5">
                Evento: {ev.detalhe.evento || "—"} | Estilo: {ev.detalhe.estilo || "—"}
              </div>
            )}
          </div>
        );
      case "followup_enviado":
        return (
          <div>
            <span className="font-semibold text-neutral-900">Follow-up automático enviado</span>
            {ev.detalhe?.mensagem && <p className="text-xs text-neutral-500 italic mt-0.5">"{ev.detalhe.mensagem}"</p>}
          </div>
        );
      case "transbordo_aberto":
        return (
          <div>
            <span className="font-semibold text-purple-900">Transbordo aberto</span>
            <p className="text-xs text-purple-700">Conversa encaminhada para atendimento humano.</p>
          </div>
        );
      case "transbordo_assumido":
        return (
          <div>
            <span className="font-semibold text-purple-900">Atendente assumiu a conversa</span>
            <p className="text-xs text-purple-700">IA pausada temporariamente (30 min).</p>
          </div>
        );
      case "transbordo_devolvido":
        return (
          <div>
            <span className="font-semibold text-neutral-900">Conversa devolvida para a IA</span>
            <p className="text-xs text-neutral-500">Automação retomada com sucesso.</p>
          </div>
        );
      case "agendou":
        return (
          <div>
            <span className="font-semibold text-teal-900">Agendamento criado na WebLocação</span>
            {ev.detalhe && (
              <p className="text-xs text-teal-800 font-mono mt-0.5">
                {ev.detalhe.tipo} - {ev.detalhe.data} às {ev.detalhe.hora}
              </p>
            )}
          </div>
        );
      case "descartado":
        return (
          <div>
            <span className="font-semibold text-rose-900">Lead descartado</span>
            {ev.motivo && <p className="text-xs text-rose-700 mt-0.5">Motivo: {ev.motivo}</p>}
          </div>
        );
      case "divergencia_ia_humano":
        return (
          <div>
            <span className="font-semibold text-amber-900">Divergência de status (MV3)</span>
            <p className="text-xs text-amber-700">Movimentação humana recente mantida.</p>
          </div>
        );
      case "nota":
        return (
          <div>
            <span className="font-semibold text-neutral-900">Nota de Atendimento</span>
            {ev.motivo && <p className="text-xs text-neutral-600 mt-0.5">{ev.motivo}</p>}
          </div>
        );
      default:
        return <span className="font-semibold text-neutral-900">Evento de sistema</span>;
    }
  };

  return (
    <div className="space-y-4 rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
      {/* Header com Tags (AC 2, AC 10.7) */}
      <div className="flex items-center justify-between border-b border-neutral-200 pb-3">
        <h3 className="text-sm font-bold text-neutral-900">Timeline de Eventos — {nomeLead}</h3>
        <div className="flex items-center gap-1.5">
          {tags.map((tag, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-1 rounded-md bg-neutral-100 px-2 py-0.5 text-[11px] font-semibold text-neutral-700"
            >
              <Tag className="h-3 w-3 text-neutral-400" />
              {tag}
            </span>
          ))}
          {tags.length === 0 && (
            <span className="text-xs text-neutral-400 italic">Sem tags</span>
          )}
        </div>
      </div>

      {/* Lista Cronológica (criado_em desc - AC 3) */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-neutral-200">
        {eventos.map((ev) => (
          <div key={ev.id} className="relative flex items-start gap-3 text-xs">
            {/* Ícone Indicador */}
            <div className="absolute -left-6 top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-white border border-neutral-200 shadow-xs">
              {renderIconeEvento(ev.tipo)}
            </div>

            {/* Detalhes do Evento */}
            <div className="flex-1 rounded-lg border border-neutral-100 bg-neutral-50/50 p-2.5 space-y-1">
              <div className="flex items-center justify-between">
                {renderConteudoEvento(ev)}
                <span className="text-[10px] text-neutral-400 font-mono ml-2">
                  {new Date(ev.criado_em).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            </div>
          </div>
        ))}

        {eventos.length === 0 && (
          <div className="py-6 text-center text-xs text-neutral-400 italic">
            Nenhum evento registrado na timeline.
          </div>
        )}
      </div>
    </div>
  );
}
