import React, { useState } from 'react';
import { INITIAL_CONTACTS } from '../../data/mockData';
import { Badge } from '../common/Badge';
import { Users, Filter, Megaphone } from 'lucide-react';

interface ContactsViewProps {
  onShowToast: (title: string, subtitle?: string) => void;
}

export const ContactsView: React.FC<ContactsViewProps> = ({ onShowToast }) => {
  const [eventFilter, setEventFilter] = useState<string>('');
  const [monthFilter, setMonthFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const filtered = INITIAL_CONTACTS.filter((item) => {
    return (
      (!eventFilter || item.event === eventFilter) &&
      (!monthFilter || item.month === monthFilter) &&
      (!statusFilter || item.status === statusFilter)
    );
  });

  const segmentSize = Math.round((filtered.length / INITIAL_CONTACTS.length) * 1284);

  const handleCreateCampaign = () => {
    onShowToast('Campanha Criada', `Segmento de ${segmentSize.toLocaleString('pt-BR')} contatos selecionados.`);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Segment KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs">
          <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold block">
            Contatos na Base
          </span>
          <div className="font-serif text-3xl font-medium text-slate-900 my-1">1.284</div>
          <span className="text-xs text-slate-500">inclui leads descartados</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[#0E4A7B] font-bold block">
            Segmento Selecionado
          </span>
          <div className="font-serif text-3xl font-medium text-[#0E4A7B] my-1">
            {segmentSize.toLocaleString('pt-BR')}
          </div>
          <span className="text-xs text-slate-500">pelos filtros ativos</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[#7B2233] font-bold block">
            Opt-out Respeitados
          </span>
          <div className="font-serif text-3xl font-medium text-[#7B2233] my-1">37</div>
          <span className="text-xs text-slate-500">nunca entram em campanha</span>
        </div>
      </div>

      {/* Segment Filters Toolbar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 flex flex-wrap items-end justify-between gap-4 shadow-2xs">
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div>
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold block mb-1">
              Tipo de Evento
            </label>
            <select
              value={eventFilter}
              onChange={(e) => setEventFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:border-[#0E4A7B]"
            >
              <option value="">Todos os eventos</option>
              <option value="Casamento">Casamento</option>
              <option value="Formatura">Formatura</option>
              <option value="15 anos">15 anos</option>
            </select>
          </div>

          <div>
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold block mb-1">
              Mês do Evento
            </label>
            <select
              value={monthFilter}
              onChange={(e) => setMonthFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:border-[#0E4A7B]"
            >
              <option value="">Todos os meses</option>
              <option value="Setembro">Setembro</option>
              <option value="Outubro">Outubro</option>
              <option value="Novembro">Novembro</option>
              <option value="Dezembro">Dezembro</option>
            </select>
          </div>

          <div>
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold block mb-1">
              Status Final
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:border-[#0E4A7B]"
            >
              <option value="">Todos os status</option>
              <option value="Descartado">Descartado</option>
              <option value="Ganho">Ganho</option>
              <option value="Ativo">Ativo</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleCreateCampaign}
          className="bg-[#0E4A7B] hover:bg-[#072F53] text-white px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 shadow-sm transition-colors"
        >
          <Megaphone className="w-4 h-4" /> Criar Campanha de Remarketing
        </button>
      </div>

      {/* Contacts Directory Table */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-2xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-semibold text-xs text-slate-900">Base de Contatos Filtrada</h3>
          <span className="text-xs text-slate-400">
            Amostra de {filtered.length} de {INITIAL_CONTACTS.length} registros
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#FAF7F2] font-mono text-[9px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
              <tr>
                <th className="px-4 py-3">Contato</th>
                <th className="px-4 py-3">Evento</th>
                <th className="px-4 py-3">Mês</th>
                <th className="px-4 py-3">Interesse</th>
                <th className="px-4 py-3">Status Final</th>
                <th className="px-4 py-3">Último Contato</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((r, idx) => (
                <tr key={idx} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 font-semibold text-slate-900">{r.name}</td>
                  <td className="px-4 py-3 text-slate-600">{r.event}</td>
                  <td className="px-4 py-3 text-slate-600">{r.month}</td>
                  <td className="px-4 py-3 text-slate-700 font-medium">{r.interest}</td>
                  <td className="px-4 py-3">
                    <Badge
                      variant={
                        r.status === 'Ganho' ? 'sage' : r.status === 'Ativo' ? 'gold' : 'mut'
                      }
                    >
                      {r.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-400">{r.lastContact}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
