import React from 'react';
import { 
  Kanban, 
  MessageSquare, 
  Calendar, 
  Users, 
  Cpu, 
  Radio, 
  BarChart3, 
  Star, 
  LogOut,
  Sparkles
} from 'lucide-react';
import { NavigationPage } from '../../types';

interface SidebarProps {
  activePage: NavigationPage;
  onNavigate: (page: NavigationPage) => void;
  activeChannelName: string;
  activeChannelPhone: string;
  unreadCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onNavigate,
  activeChannelName,
  activeChannelPhone,
  unreadCount = 1,
}) => {
  const navItems: { id: NavigationPage; label: string; icon: React.ReactNode; cnt?: number; section?: string }[] = [
    { id: 'crm', label: 'Pipeline', icon: <Kanban className="w-4 h-4" />, section: 'Operação' },
    { id: 'att', label: 'Atendimento', icon: <MessageSquare className="w-4 h-4" />, cnt: unreadCount },
    { id: 'agenda', label: 'Agenda', icon: <Calendar className="w-4 h-4" /> },
    { id: 'base', label: 'Base de Contatos', icon: <Users className="w-4 h-4" /> },
    { id: 'reports', label: 'Relatórios Executive', icon: <BarChart3 className="w-4 h-4" />, section: 'Análise & Visão' },
    { id: 'auto', label: 'Automações IA', icon: <Cpu className="w-4 h-4" />, section: 'Configuração' },
    { id: 'canal', label: 'Canal WhatsApp', icon: <Radio className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-full lg:w-64 bg-gradient-to-b from-[#072F53] via-[#0E4A7B] to-[#083358] text-white flex flex-col h-screen sticky top-0 border-r border-[#1868A8]/30 shadow-xl z-20">
      {/* Logo Header */}
      <div className="p-5 border-b border-[#1868A8]/30">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#EBB832] to-[#A67C2E] grid place-items-center shadow-lg text-[#072F53] font-bold">
            <Sparkles className="w-5 h-5 text-[#072F53]" />
          </div>
          <div>
            <h1 className="font-serif text-2xl font-normal tracking-wider text-white leading-none">
              ALFAIA
            </h1>
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#EBB832] font-semibold block mt-1">
              Atendimento + CRM
            </span>
          </div>
        </div>
      </div>

      {/* User Avatar Card (From JPG Concept) */}
      <div className="mx-3 my-3 p-3 rounded-xl bg-white/10 backdrop-blur-md border border-white/10 flex items-center gap-3">
        <div className="relative">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#EBB832] to-[#F2E7D0] text-[#072F53] font-bold grid place-items-center text-sm shadow">
            JP
          </div>
          <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-[#072F53]"></span>
        </div>
        <div className="min-w-0 flex-1">
          <b className="block text-xs font-semibold text-white truncate">Juliana Prado</b>
          <div className="flex items-center gap-1 mt-0.5 text-[#EBB832]">
            {[...Array(5)].map((_, i) => (
              <Star key={i} className="w-2.5 h-2.5 fill-current" />
            ))}
          </div>
          <span className="text-[10px] text-slate-300 font-mono block truncate">
            Especialista WebLocação
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="px-3 py-2 flex-1 overflow-y-auto space-y-1">
        {navItems.map((item, index) => {
          const isActive = activePage === item.id;
          const showSection = item.section && (index === 0 || navItems[index - 1]?.section !== item.section);

          return (
            <React.Fragment key={item.id}>
              {showSection && (
                <div className="font-mono text-[9px] uppercase tracking-widest text-slate-300 px-3 pt-3 pb-1 font-semibold opacity-80">
                  {item.section}
                </div>
              )}
              <button
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all relative group text-left ${
                  isActive
                    ? 'bg-white text-[#072F53] font-semibold shadow-md'
                    : 'text-slate-200 hover:bg-white/10 hover:text-white'
                }`}
              >
                {isActive && (
                  <span className="absolute left-0 top-2 bottom-2 w-1 bg-[#EBB832] rounded-r"></span>
                )}
                <span className={`${isActive ? 'text-[#0E4A7B]' : 'text-slate-300 group-hover:text-white'}`}>
                  {item.icon}
                </span>
                <span className="flex-1 truncate">{item.label}</span>
                {item.cnt && item.cnt > 0 ? (
                  <span className="font-mono text-[10px] bg-[#7B2233] text-white px-1.5 py-0.5 rounded-full font-bold shadow-sm">
                    {item.cnt}
                  </span>
                ) : null}
              </button>
            </React.Fragment>
          );
        })}
      </nav>

      {/* Channel Connection Footer */}
      <div className="p-3 border-t border-[#1868A8]/30">
        <div className="p-2.5 bg-white/10 rounded-xl border border-white/15 flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse flex-shrink-0"></span>
          <div className="min-w-0 flex-1">
            <b className="block text-[11px] font-semibold text-white truncate">{activeChannelName}</b>
            <small className="font-mono text-[9px] text-slate-300 block truncate">{activeChannelPhone}</small>
          </div>
          <button className="text-slate-400 hover:text-white p-1" title="Log out">
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
};
