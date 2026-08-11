'use client';

import React, { useState } from 'react';

interface Conversa {
  id: string;
  contato_nome: string;
  telefone: string;
  estado: 'ia' | 'humano' | 'transbordo';
  ultima_mensagem: string;
  atualizado_em: string;
}

export default function ConversasPage() {
  const [conversas, setConversas] = useState<Conversa[]>([
    {
      id: 'c1',
      contato_nome: 'Mariana Silva',
      telefone: '+55 85 98811-2233',
      estado: 'transbordo',
      ultima_mensagem: 'Gostaria de falar com uma atendente para ajustar o vestido.',
      atualizado_em: '14:22',
    },
    {
      id: 'c2',
      contato_nome: 'Carla Souza',
      telefone: '+55 85 99922-3344',
      estado: 'ia',
      ultima_mensagem: 'Temos o Vestido Longo Champanhe disponível.',
      atualizado_em: '14:15',
    },
    {
      id: 'c3',
      contato_nome: 'Beatriz Lima',
      telefone: '+55 85 97733-4455',
      estado: 'humano',
      ultima_mensagem: 'Ajuste de barra confirmado para sexta-feira às 15h.',
      atualizado_em: '13:50',
    },
  ]);

  const [selecionadaId, setSelecionadaId] = useState<string>('c1');

  const conversaSelecionada = conversas.find((c) => c.id === selecionadaId);

  const assumirConversa = (id: string) => {
    setConversas((prev) =>
      prev.map((c) => (c.id === id ? { ...c, estado: 'humano' } : c))
    );
  };

  const devolverParaIA = (id: string) => {
    setConversas((prev) =>
      prev.map((c) => (c.id === id ? { ...c, estado: 'ia' } : c))
    );
  };

  const renderBadge = (estado: Conversa['estado']) => {
    if (estado === 'ia') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
          IA Atendendo
        </span>
      );
    }
    if (estado === 'transbordo') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 animate-pulse">
          Transbordo Solicitado
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-navy-100 text-[#072F53] font-semibold border border-[#072F53]/20">
        Atendimento Humano
      </span>
    );
  };

  return (
    <div className="flex h-[calc(100vh-6rem)] bg-[#FAF7F2] text-slate-800 font-sans">
      {/* Sidebar Lista de Conversas Realtime */}
      <div className="w-1/3 border-r border-[#E7DFD2] bg-white flex flex-col">
        <div className="p-4 border-b border-[#E7DFD2] bg-[#FAF7F2]">
          <h1 className="text-xl font-serif font-bold text-[#072F53]">Painel Realtime de Conversas</h1>
          <p className="text-xs text-slate-5-0 mt-1">Latência de sincronização &le; 2s (NFR9)</p>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-[#E7DFD2]">
          {conversas.map((c) => (
            <div
              key={c.id}
              onClick={() => setSelecionadaId(c.id)}
              className={`p-4 cursor-pointer transition-colors ${
                selecionadaId === c.id ? 'bg-[#FAF7F2]' : 'hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900">{c.contato_nome}</h3>
                <span className="text-xs text-slate-400">{c.atualizado_em}</span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{c.telefone}</p>
              <div className="mt-2 flex items-center justify-between">
                {renderBadge(c.estado)}
              </div>
              <p className="text-xs text-slate-600 mt-2 line-clamp-1 italic">
                "{c.ultima_mensagem}"
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Detalhe da Conversa Selecionada */}
      <div className="flex-1 flex flex-col bg-[#FAF7F2]">
        {conversaSelecionada ? (
          <>
            {/* Header da Conversa */}
            <div className="p-4 border-b border-[#E7DFD2] bg-white flex items-center justify-between shadow-sm">
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-lg font-semibold text-[#072F53]">{conversaSelecionada.contato_nome}</h2>
                  {renderBadge(conversaSelecionada.estado)}
                </div>
                <p className="text-xs text-slate-500">{conversaSelecionada.telefone}</p>
              </div>

              <div className="flex items-center gap-3">
                {conversaSelecionada.estado === 'humano' ? (
                  <button
                    onClick={() => devolverParaIA(conversaSelecionada.id)}
                    className="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-all"
                  >
                    Devolver para Atendimento IA
                  </button>
                ) : (
                  <button
                    onClick={() => assumirConversa(conversaSelecionada.id)}
                    className="px-4 py-2 text-xs font-semibold text-white bg-[#072F53] hover:bg-[#0E4A7B] rounded-lg shadow-sm transition-all"
                  >
                    Assumir Conversa (Pausar IA)
                  </button>
                )}
              </div>
            </div>

            {/* Histórico de Mensagens */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4">
              <div className="flex justify-start">
                <div className="max-w-md bg-white p-3 rounded-2xl rounded-tl-none border border-[#E7DFD2] shadow-sm">
                  <p className="text-xs text-slate-500 mb-1 font-semibold">Cliente</p>
                  <p className="text-sm">{conversaSelecionada.ultima_mensagem}</p>
                </div>
              </div>

              {conversaSelecionada.estado === 'humano' && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-center">
                  <p className="text-xs text-amber-800 font-medium">
                    ⚠️ Atendimento Humano Ativo: O motor de IA está pausado e não responderá a novas mensagens.
                  </p>
                </div>
              )}
            </div>

            {/* Input de Envio Humano */}
            <div className="p-4 border-t border-[#E7DFD2] bg-white flex items-center gap-3">
              <input
                type="text"
                placeholder={
                  conversaSelecionada.estado === 'humano'
                    ? 'Digite sua resposta como atendente humano...'
                    : 'Assuma a conversa para responder...'
                }
                disabled={conversaSelecionada.estado !== 'humano'}
                className="flex-1 px-4 py-2 border border-[#E7DFD2] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#072F53] disabled:bg-slate-100 disabled:cursor-not-allowed"
              />
              <button
                disabled={conversaSelecionada.estado !== 'humano'}
                className="px-5 py-2 text-sm font-medium text-white bg-[#072F53] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Enviar
              </button>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400">
            Selecione uma conversa para visualizar
          </div>
        )}
      </div>
    </div>
  );
}
