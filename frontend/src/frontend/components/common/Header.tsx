import React from 'react';
import { Search, Bell, Mail, Grid, MoreHorizontal, RefreshCw } from 'lucide-react';

interface HeaderProps {
  title: string;
  subtitle: string;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  actions?: React.ReactNode;
  onRefreshSync?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  searchQuery,
  onSearchChange,
  actions,
  onRefreshSync,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-10 px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs">
      <div>
        <h2 className="font-serif text-2xl md:text-3xl font-medium text-[#1F1B17] leading-tight">
          {title}
        </h2>
        <p className="text-xs text-slate-500 font-sans mt-0.5">{subtitle}</p>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        {/* Search Input matching JPG Concept */}
        <div className="relative min-w-[220px] lg:min-w-[280px]">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Buscar lead, telefone ou traje..."
            className="w-full bg-[#F3F6F9] border border-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-xs focus:outline-none focus:border-[#0E4A7B] focus:bg-white transition-all text-slate-800"
          />
        </div>

        {/* Action icons from JPG Header */}
        <div className="flex items-center gap-1.5 border-l border-slate-200 pl-3">
          <button
            onClick={onRefreshSync}
            className="p-1.5 text-slate-500 hover:text-[#0E4A7B] hover:bg-slate-100 rounded-lg transition-colors relative"
            title="Sincronizar dados WebLocação"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button className="p-1.5 text-slate-500 hover:text-[#0E4A7B] hover:bg-slate-100 rounded-lg transition-colors relative">
            <Mail className="w-4 h-4" />
          </button>
          <button className="p-1.5 text-slate-500 hover:text-[#0E4A7B] hover:bg-slate-100 rounded-lg transition-colors relative">
            <Bell className="w-4 h-4" />
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#7B2233]"></span>
          </button>
          <button className="p-1.5 text-slate-500 hover:text-[#0E4A7B] hover:bg-slate-100 rounded-lg transition-colors">
            <Grid className="w-4 h-4" />
          </button>
          <button className="p-1.5 text-slate-500 hover:text-[#0E4A7B] hover:bg-slate-100 rounded-lg transition-colors">
            <MoreHorizontal className="w-4 h-4" />
          </button>
        </div>

        {/* Custom View Actions */}
        {actions && <div className="flex items-center gap-2 border-l border-slate-200 pl-3">{actions}</div>}
      </div>
    </header>
  );
};
