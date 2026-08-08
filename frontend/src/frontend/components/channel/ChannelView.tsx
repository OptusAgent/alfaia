import React, { useState } from 'react';
import { PROVIDERS } from '../../data/mockData';
import { Badge } from '../common/Badge';
import { Radio, Info, CheckCircle2, ShieldCheck, AlertTriangle } from 'lucide-react';

interface ChannelViewProps {
  activeChannelKey: string;
  onSelectChannel: (key: string) => void;
  onShowToast: (title: string, subtitle?: string) => void;
}

export const ChannelView: React.FC<ChannelViewProps> = ({
  activeChannelKey,
  onSelectChannel,
  onShowToast,
}) => {
  const currentProvider = PROVIDERS.find((p) => p.k === activeChannelKey) || PROVIDERS[0];

  const handleSwitch = (key: string) => {
    if (key === activeChannelKey) return;
    onSelectChannel(key);
    const p = PROVIDERS.find((x) => x.k === key);
    if (p) {
      onShowToast('Canal WhatsApp Alterado', `${p.n} passa a valer na próxima mensagem.`);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Information Banner */}
      <div className="bg-[#E5EDF3] border border-[#4A6B84]/20 text-[#1F1B17] p-4 rounded-2xl flex items-start gap-3 text-xs leading-relaxed shadow-2xs">
        <Info className="w-5 h-5 text-[#4A6B84] flex-shrink-0 mt-0.5" />
        <div>
          <b>Arquitetura de Provedores Agnosticos:</b> Os dois provedores de WhatsApp estão integrados no backend do ALFAIA. A troca de provedor tem efeito imediato e preserva todo o histórico de conversas do pipeline.
        </div>
      </div>

      {/* Provider Selector Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PROVIDERS.map((prov) => {
          const isActive = prov.k === activeChannelKey;
          return (
            <div
              key={prov.k}
              onClick={() => handleSwitch(prov.k)}
              className={`bg-white border-2 rounded-2xl p-5 cursor-pointer transition-all relative ${
                isActive
                  ? 'border-[#0E4A7B] bg-gradient-to-br from-[#E2EDF8] to-white shadow-md'
                  : 'border-slate-200 hover:border-[#0E4A7B]/40'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-xl grid place-items-center font-bold text-white shadow-2xs"
                    style={{ backgroundColor: prov.ic }}
                  >
                    <Radio className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-serif text-xl font-semibold text-slate-900">{prov.n}</h3>
                    <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400 block">
                      {prov.s}
                    </span>
                  </div>
                </div>

                <Badge variant={isActive ? 'sage' : 'mut'}>
                  {isActive ? 'Ativo na Loja' : 'Configurado'}
                </Badge>
              </div>

              <div className="font-mono text-xs text-slate-500 mb-4">{prov.phone}</div>

              <div className="space-y-1.5 text-xs border-t border-slate-100 pt-3">
                {prov.caps.map(([cap, val, flag], idx) => (
                  <div key={idx} className="flex justify-between items-center py-0.5">
                    <span className="text-slate-500">{cap}</span>
                    <span
                      className={`font-semibold ${
                        flag === 'y'
                          ? 'text-[#4B7A5B]'
                          : flag === 'r'
                          ? 'text-[#7B2233]'
                          : 'text-slate-600'
                      }`}
                    >
                      {val}
                    </span>
                  </div>
                ))}
              </div>

              <button
                disabled={isActive}
                className={`w-full mt-4 py-2.5 rounded-xl font-semibold text-xs transition-all ${
                  isActive
                    ? 'bg-[#4B7A5B] text-white cursor-default'
                    : 'bg-[#0E4A7B] text-white hover:bg-[#072F53] shadow-xs'
                }`}
              >
                {isActive ? 'Canal Ativo na Operação' : 'Ativar Este Canal'}
              </button>
            </div>
          );
        })}
      </div>

      {/* Normalized Webhook Payload Inspector */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs">
        <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-3">
          <h3 className="font-serif text-lg font-semibold text-slate-900">
            Contrato Normalizado de Evento WhatsApp
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            Provedor ativo: <b className="text-[#0E4A7B]">{currentProvider.n}</b>
          </span>
        </div>

        <pre className="bg-[#FAF7F2] border border-slate-200 rounded-xl p-4 font-mono text-xs text-slate-800 leading-relaxed overflow-x-auto">
{`{
  "tenant_id"      : "8f321a44-b0a1-4322-91f8-009121fa9112",
  "canal_id"       : "whatsapp-oficial-main",
  "provider"       : "${activeChannelKey}",
  "telefone"       : "5585988124477",
  "push_name"      : "Marcela Prado",
  "mensagem"       : "tenho um casamento dia 12/09 procuro vestido longo...",
  "midia_tipo"     : "text",
  "wa_message_id"  : "${
    activeChannelKey === 'meta'
      ? 'wamid.HBgMNTU4NTk4ODEyNDQ3N1UCMRU0OUUxMzE0OUE4'
      : '3EB0B5FABDBBF09DA87A'
  }",
  "data_atual"     : "Sábado, 8 de agosto de 2026, 21:48"
}`}
        </pre>
      </div>
    </div>
  );
};
