import React from 'react';
import { Lead, LeadStatus } from '../../types';
import { Badge } from '../common/Badge';
import { Clock, Send, Flame, Snowflake } from 'lucide-react';

interface LeadCardProps {
  lead: Lead;
  onOpenLead: (id: string) => void;
  onTriggerFollowUp: (id: string) => void;
  onDragStart: (e: React.DragEvent, id: string) => void;
  onDragEnd: (e: React.DragEvent) => void;
}

export const LeadCard: React.FC<LeadCardProps> = ({
  lead,
  onOpenLead,
  onTriggerFollowUp,
  onDragStart,
  onDragEnd,
}) => {
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .slice(0, 2)
      .join('');
  };

  const isCold = lead.cold || lead.st === 'follow_up';

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, lead.id)}
      onDragEnd={onDragEnd}
      onClick={() => onOpenLead(lead.id)}
      className={`bg-white border rounded-xl p-3 cursor-grab active:cursor-grabbing hover:-translate-y-1 hover:shadow-md transition-all group ${
        isCold ? 'border-l-4 border-l-[#7B2233] border-slate-200' : lead.hot ? 'border-l-4 border-l-[#4B7A5B] border-slate-200' : 'border-slate-200'
      }`}
    >
      <div className="flex items-center gap-2.5 mb-1.5">
        <div className="w-7 h-7 rounded-full bg-[#EFE9DE] text-[#1F1B17] font-bold text-xs grid place-items-center flex-shrink-0">
          {getInitials(lead.n)}
        </div>
        <div className="min-w-0 flex-1 flex items-center justify-between">
          <b className="text-xs font-semibold text-slate-900 truncate">{lead.n}</b>
          {lead.hot && <Flame className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" title="Hot lead" />}
          {isCold && <Snowflake className="w-3.5 h-3.5 text-[#7B2233] flex-shrink-0" title="Aguardando follow-up" />}
        </div>
      </div>

      <div className="text-[11px] text-slate-500 leading-snug">
        <span>{lead.ev}</span>
        {lead.pc !== '—' && <span className="block text-slate-700 font-medium">{lead.pc}</span>}
      </div>

      <div className="flex flex-wrap gap-1 mt-2">
        <Badge variant="mut">{lead.or}</Badge>
        {lead.v > 0 && <Badge variant="sage">R$ {lead.v}</Badge>}
        {lead.ag && <Badge variant="gold">{lead.ag}</Badge>}
      </div>

      <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-slate-100 text-[10px] text-slate-400">
        <span className="flex items-center gap-1 font-mono">
          <Clock className="w-3 h-3 text-slate-400" /> há {lead.h}
        </span>

        {lead.st === 'follow_up' && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onTriggerFollowUp(lead.id);
            }}
            className="bg-[#7B2233] hover:bg-[#5E1A27] text-white px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 transition-colors shadow-xs"
          >
            <Send className="w-2.5 h-2.5" /> Disparar {lead.fu ? `(${lead.fu}ª)` : ''}
          </button>
        )}
      </div>
    </div>
  );
};
