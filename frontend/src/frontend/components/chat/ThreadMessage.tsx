import React from 'react';
import { ProductItem } from '../../types';
import { ProductCard } from './ProductCard';

interface ThreadMessageProps {
  actor: 'cli' | 'ia' | 'ag' | 'sys';
  text?: string;
  time: string;
  products?: ProductItem[];
}

export const ThreadMessage: React.FC<ThreadMessageProps> = ({ actor, text, time, products }) => {
  const actorConfigs = {
    cli: { label: 'LEAD / CLIENTE', border: 'border-l-slate-400', bg: 'bg-[#FAF7F2]', textCol: 'text-slate-500' },
    ia: { label: 'ALFAIA IA', border: 'border-l-[#4B7A5B]', bg: 'bg-[#E5EFE7]', textCol: 'text-[#4B7A5B]' },
    ag: { label: 'ATENDENTE (JULIANA)', border: 'border-l-[#A67C2E]', bg: 'bg-[#F2E7D0]', textCol: 'text-[#A67C2E]' },
    sys: { label: 'SISTEMA WEBLOCAÇÃO', border: 'border-l-[#7B2233]', bg: 'bg-[#F7E8EA]', textCol: 'text-[#7B2233]' },
  };

  const cfg = actorConfigs[actor];

  return (
    <div className="flex gap-3 animate-fade-in my-2">
      <span className="font-mono text-[10px] text-slate-400 w-10 flex-shrink-0 pt-1 text-right">{time}</span>
      <div className="flex-1 min-w-0">
        <span className={`font-mono text-[9px] font-bold tracking-wider uppercase block mb-1 ${cfg.textCol}`}>
          {cfg.label}
        </span>

        <div className={`p-3 rounded-xl border-l-2 text-xs leading-relaxed whitespace-pre-wrap ${cfg.border} ${cfg.bg} text-slate-800 shadow-2xs`}>
          {text}

          {products && products.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-3">
              {products.map((p, idx) => (
                <ProductCard key={idx} product={p} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
