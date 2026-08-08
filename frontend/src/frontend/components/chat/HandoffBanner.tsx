import React from 'react';
import { AlertCircle, UserCheck, Bot } from 'lucide-react';

interface HandoffBannerProps {
  isOpen: boolean;
  isTaken: boolean;
  onTakeover: () => void;
  onReturnToAI: () => void;
}

export const HandoffBanner: React.FC<HandoffBannerProps> = ({
  isOpen,
  isTaken,
  onTakeover,
  onReturnToAI,
}) => {
  if (!isOpen) return null;

  return (
    <div
      className={`mx-5 mb-3 p-3.5 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 animate-fade-in text-xs ${
        isTaken
          ? 'bg-[#F2E7D0] border-[#A67C2E]/40 text-[#1F1B17]'
          : 'bg-[#F7E8EA] border-[#7B2233]/40 text-[#7B2233]'
      }`}
    >
      <div className="flex items-center gap-2.5">
        <AlertCircle className="w-5 h-5 flex-shrink-0" />
        <div>
          <b className="block text-xs font-semibold text-slate-900">
            {isTaken ? 'Juliana assumiu a conversa' : 'Transbordo Solicitado — Aguardando Atendente'}
          </b>
          <small className="text-[11px] opacity-80 block mt-0.5">
            {isTaken
              ? 'IA pausada. Ela só volta a atuar quando você devolver o controle.'
              : 'A IA pausou a automação e aguarda a intervenção do humano.'}
          </small>
        </div>
      </div>

      <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
        {!isTaken ? (
          <button
            onClick={onTakeover}
            className="bg-[#7B2233] hover:bg-[#5E1A27] text-white px-3 py-1.5 rounded-lg font-semibold text-xs flex items-center gap-1.5 shadow-2xs transition-colors"
          >
            <UserCheck className="w-3.5 h-3.5" /> Assumir Conversa
          </button>
        ) : (
          <button
            onClick={onReturnToAI}
            className="bg-[#0E4A7B] hover:bg-[#072F53] text-white px-3 py-1.5 rounded-lg font-semibold text-xs flex items-center gap-1.5 shadow-2xs transition-colors"
          >
            <Bot className="w-3.5 h-3.5" /> Devolver para a IA
          </button>
        )}
      </div>
    </div>
  );
};
