'use client';

import React, { useState, useEffect } from 'react';
import { Badge } from '@/app/components/ui/Badge';
import { Send } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';

interface Conversa {
  id: string;
  contato_nome: string;
  telefone: string;
  estado: 'ia' | 'humano' | 'transbordo';
  ultima_mensagem: string;
  atualizado_em: string;
}

interface DbConversaItem {
  id: string;
  estado: 'ia' | 'humano' | 'transbordo';
  criada_em: string;
  contatos?: { nome?: string; telefone?: string };
  mensagens?: { texto: string; enviado_em: string }[];
}

export default function ConversasPage() {
  const [conversas, setConversas] = useState<Conversa[]>([]);
  const [selecionadaId, setSelecionadaId] = useState<string>('');
  const [novoTexto, setNovoTexto] = useState<string>('');

  const supabase = createClient();

  async function fetchConversasEReais() {
    try {
      const { data: dbConversas } = await supabase
        .from('conversas')
        .select(`
          id,
          estado,
          criada_em,
          contatos ( nome, telefone ),
          mensagens ( texto, enviado_em )
        `)
        .order('criada_em', { ascending: false });

      if (dbConversas && dbConversas.length > 0) {
        const canaisMapped: Conversa[] = (dbConversas as unknown as DbConversaItem[]).map((item) => {
          const contato = item.contatos || {};
          const msgs = item.mensagens || [];
          const ultimaMsg = msgs.length > 0 ? msgs[msgs.length - 1].texto : 'Nova conversa iniciada';
          const hora = msgs.length > 0
            ? new Date(msgs[msgs.length - 1].enviado_em).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : new Date(item.criada_em).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

          return {
            id: item.id,
            contato_nome: contato.nome || 'Cliente WhatsApp',
            telefone: contato.telefone || 'WhatsApp',
            estado: item.estado || 'ia',
            ultima_mensagem: ultimaMsg,
            atualizado_em: hora,
          };
        });

        setConversas(canaisMapped);
        if (!selecionadaId && canaisMapped.length > 0) {
          setSelecionadaId(canaisMapped[0].id);
        }
      } else {
        // Mock fallback se o banco ainda não possuir mensagens registradas
        setConversas([
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
        ]);
        if (!selecionadaId) setSelecionadaId('c1');
      }
    } catch {
      //
    } finally {
      setLoading(false);
    }
  }

  // Inscreve no Supabase Realtime para escutar mensagens e conversas em tempo real (latência <= 2s)
  useEffect(() => {
    fetchConversasEReais();

    const channel = supabase
      .channel('realtime-conversas-live')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'mensagens' },
        () => {
          fetchConversasEReais();
        }
      )
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'conversas' },
        () => {
          fetchConversasEReais();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const conversaSelecionada = conversas.find((c) => c.id === selecionadaId);

  const assumirConversa = async (id: string) => {
    setConversas((prev) =>
      prev.map((c) => (c.id === id ? { ...c, estado: 'humano' } : c))
    );
    try {
      await supabase.from('conversas').update({ estado: 'humano' }).eq('id', id);
    } catch {
      //
    }
  };

  const devolverParaIA = async (id: string) => {
    setConversas((prev) =>
      prev.map((c) => (c.id === id ? { ...c, estado: 'ia' } : c))
    );
    try {
      await supabase.from('conversas').update({ estado: 'ia' }).eq('id', id);
    } catch {
      //
    }
  };

  const handleEnviarMensagem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!novoTexto.trim() || !conversaSelecionada) return;

    setEnviando(true);
    try {
      const texto = novoTexto;
      setNovoTexto('');
      setMensagens((prev) => [
        ...prev,
        { id: Date.now(), remetente: 'atendente', texto, enviado_em: new Date().toISOString() },
      ]);
    } catch {
      //
    } finally {
      setEnviando(false);
    }
  };

  const renderBadge = (estado: Conversa['estado']) => {
    if (estado === 'ia') {
      return <Badge variant="success">IA Atendendo</Badge>;
    }
    if (estado === 'transbordo') {
      return <Badge variant="warning" pulse>Transbordo Solicitado</Badge>;
    }
    return <Badge variant="purple">Atendimento Humano</Badge>;
  };

  return (
    <div
      className="flex h-[calc(100vh-6rem)] rounded-xl overflow-hidden"
      style={{
        background: "var(--bg-surface)",
        border: "1px solid rgba(255, 255, 255, 0.06)",
      }}
    >
      {/* Sidebar Lista de Conversas */}
      <div
        className="w-1/3 flex flex-col"
        style={{ borderRight: "1px solid rgba(255, 255, 255, 0.06)" }}
      >
        <div
          className="p-4"
          style={{
            borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
            background: "rgba(255, 255, 255, 0.02)",
          }}
        >
          <h1
            className="text-lg font-display font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            Conversas em Tempo Real
          </h1>
          <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
            Latência de sincronização ≤ 2s
          </p>
        </div>

        <div className="flex-1 overflow-y-auto">
          {conversas.map((c) => (
            <div
              key={c.id}
              onClick={() => setSelecionadaId(c.id)}
              className="p-4 cursor-pointer transition-all"
              style={{
                borderBottom: "1px solid rgba(255, 255, 255, 0.03)",
                background:
                  selecionadaId === c.id
                    ? "rgba(16, 185, 129, 0.06)"
                    : "transparent",
                borderLeft:
                  selecionadaId === c.id
                    ? "3px solid var(--accent-primary)"
                    : "3px solid transparent",
              }}
            >
              <div className="flex items-center justify-between">
                <h3
                  className="font-semibold text-sm"
                  style={{ color: "var(--text-primary)" }}
                >
                  {c.contato_nome}
                </h3>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {c.atualizado_em}
                </span>
              </div>
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                {c.telefone}
              </p>
              <div className="mt-2">{renderBadge(c.estado)}</div>
              <p
                className="text-xs mt-2 line-clamp-1 italic"
                style={{ color: "var(--text-secondary)" }}
              >
                &quot;{c.ultima_mensagem}&quot;
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Detalhe da Conversa */}
      <div className="flex-1 flex flex-col" style={{ background: "var(--bg-primary)" }}>
        {conversaSelecionada ? (
          <>
            {/* Header */}
            <div
              className="p-4 flex items-center justify-between"
              style={{
                borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
                background: "rgba(255, 255, 255, 0.02)",
              }}
            >
              <div>
                <div className="flex items-center gap-3">
                  <h2
                    className="text-base font-semibold font-display"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {conversaSelecionada.contato_nome}
                  </h2>
                  {renderBadge(conversaSelecionada.estado)}
                </div>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {conversaSelecionada.telefone}
                </p>
              </div>

              <div className="flex items-center gap-3">
                {conversaSelecionada.estado === 'humano' ? (
                  <button
                    onClick={() => devolverParaIA(conversaSelecionada.id)}
                    className="glass-btn glass-btn-primary text-xs"
                  >
                    Devolver para IA
                  </button>
                ) : (
                  <button
                    onClick={() => assumirConversa(conversaSelecionada.id)}
                    className="glass-btn glass-btn-ghost text-xs"
                    style={{
                      borderColor: "rgba(16, 185, 129, 0.3)",
                      color: "var(--accent-primary)",
                    }}
                  >
                    Assumir Conversa
                  </button>
                )}
              </div>
            </div>

            {/* Mensagens */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4">
              <div className="flex justify-start">
                <div
                  className="max-w-md p-3 rounded-2xl rounded-tl-none"
                  style={{
                    background: "rgba(255, 255, 255, 0.06)",
                    border: "1px solid rgba(255, 255, 255, 0.06)",
                  }}
                >
                  <p className="text-xs mb-1 font-semibold" style={{ color: "var(--accent-primary)" }}>
                    Cliente
                  </p>
                  <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                    {conversaSelecionada.ultima_mensagem}
                  </p>
                </div>
              </div>

              {conversaSelecionada.estado === 'humano' && (
                <div
                  className="p-3 rounded-xl text-center"
                  style={{
                    background: "var(--accent-amber-muted)",
                    border: "1px solid var(--accent-amber-border)",
                  }}
                >
                  <p className="text-xs font-medium" style={{ color: "var(--accent-amber)" }}>
                    ⚠️ Atendimento Humano Ativo: O motor de IA está pausado.
                  </p>
                </div>
              )}
            </div>

            {/* Input */}
            <div
              className="p-4 flex items-center gap-3"
              style={{
                borderTop: "1px solid rgba(255, 255, 255, 0.06)",
                background: "rgba(255, 255, 255, 0.02)",
              }}
            >
              <input
                type="text"
                placeholder={
                  conversaSelecionada.estado === 'humano'
                    ? 'Digite sua resposta como atendente humano...'
                    : 'Assuma a conversa para responder...'
                }
                disabled={conversaSelecionada.estado !== 'humano'}
                className="glass-input flex-1"
              />
              <button
                disabled={conversaSelecionada.estado !== 'humano'}
                className="glass-btn glass-btn-primary px-4"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </>
        ) : (
          <div
            className="flex-1 flex items-center justify-center"
            style={{ color: "var(--text-muted)" }}
          >
            Selecione uma conversa para visualizar
          </div>
        )}
      </div>
    </div>
  );
}
