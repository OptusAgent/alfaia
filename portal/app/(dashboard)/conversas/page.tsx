"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/app/components/ui/Badge";
import { Send } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

interface Conversa {
  id: string;
  contato_nome: string;
  telefone: string;
  estado: "ia" | "humano" | "transbordo";
  ultima_mensagem: string;
  atualizado_em: string;
}

interface MensagemLocal {
  id: string | number;
  remetente: "cliente" | "atendente" | "ia";
  texto: string;
  enviado_em: string;
}

interface DbConversaItem {
  id: string;
  tenant_id: string;
  estado: "ia" | "humano" | "transbordo";
  criada_em: string;
  ativada_em?: string | null;
  contatos?: { nome?: string; telefone?: string };
  leads?: { id?: string; status?: string; evento_tipo?: string | null; peca_interesse?: string | null };
  mensagens?: {
    id?: string | number;
    remetente?: "lead" | "ia" | "atendente" | "sistema";
    texto?: string | null;
    conteudo?: string | null;
    de_mim?: boolean | null;
    enviado_em?: string | null;
    criado_em?: string | null;
  }[];
}

export default function ConversasPage() {
  const [conversas, setConversas] = useState<Conversa[]>([]);
  const [selecionadaId, setSelecionadaId] = useState("");
  const [novoTexto, setNovoTexto] = useState("");
  const [mensagens, setMensagens] = useState<Record<string, MensagemLocal[]>>({});
  const [tenantId, setTenantId] = useState("");
  const supabase = useMemo(() => createClient(), []);

  useEffect(() => {
    async function fetchTenantAtivo() {
      const res = await fetch("/api/tenant/active", { cache: "no-store" });
      if (!res.ok) return "";
      const data = await res.json();
      return String(data.tenant_id || "");
    }

    async function fetchConversasEReais(activeTenantId: string) {
      if (!activeTenantId) {
        setConversas([]);
        setMensagens({});
        setSelecionadaId("");
        return;
      }

      try {
        const { data: dbConversas } = await supabase
          .from("conversas")
          .select(`
            id,
            tenant_id,
            estado,
            criada_em,
            ativada_em,
            contatos ( nome, telefone ),
            leads ( id, status, evento_tipo, peca_interesse ),
            mensagens ( id, remetente, texto, conteudo, de_mim, enviado_em, criado_em )
          `)
          .eq("tenant_id", activeTenantId)
          .order("criada_em", { ascending: false });

        if (dbConversas && dbConversas.length > 0) {
          const mensagensPorConversa: Record<string, MensagemLocal[]> = {};
          const mapped: Conversa[] = (dbConversas as unknown as DbConversaItem[]).map((item) => {
            const contato = item.contatos || {};
            const msgs = [...(item.mensagens || [])].sort((a, b) => {
              const aDate = new Date(a.enviado_em || a.criado_em || item.criada_em).getTime();
              const bDate = new Date(b.enviado_em || b.criado_em || item.criada_em).getTime();
              return aDate - bDate;
            });
            const ultima = msgs.at(-1);
            mensagensPorConversa[item.id] = msgs.map((msg, index) => {
              const enviadoEm = msg.enviado_em || msg.criado_em || item.criada_em;
              const remetente = msg.remetente === "ia" || msg.de_mim
                ? "ia"
                : msg.remetente === "atendente"
                  ? "atendente"
                  : "cliente";
              return {
                id: msg.id || `${item.id}-${index}`,
                remetente,
                texto: msg.texto || msg.conteudo || "",
                enviado_em: new Date(enviadoEm).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
              };
            }).filter((msg) => msg.texto);

            const hora = ultima
              ? new Date(ultima.enviado_em || ultima.criado_em || item.criada_em).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
              : new Date(item.ativada_em || item.criada_em).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

            return {
              id: item.id,
              contato_nome: contato.nome || "Cliente WhatsApp",
              telefone: contato.telefone || "WhatsApp",
              estado: item.estado || "ia",
              ultima_mensagem: ultima?.texto || ultima?.conteudo || "Nova conversa iniciada",
              atualizado_em: hora,
            };
          });

          setConversas(mapped);
          setMensagens(mensagensPorConversa);
          setSelecionadaId((current) => current || mapped[0]?.id || "");
          return;
        }
      } catch {
        setConversas([]);
        setMensagens({});
        setSelecionadaId("");
        return;
      }

      setConversas([]);
      setMensagens({});
      setSelecionadaId("");
    }

    let channel: ReturnType<typeof supabase.channel> | null = null;
    let mounted = true;

    void fetchTenantAtivo().then((activeTenantId) => {
      if (!mounted) return;
      setTenantId(activeTenantId);
      void fetchConversasEReais(activeTenantId);

      if (!activeTenantId) return;
      channel = supabase
        .channel(`realtime-conversas-live-${activeTenantId}`)
        .on("postgres_changes", { event: "*", schema: "public", table: "mensagens", filter: `tenant_id=eq.${activeTenantId}` }, () => {
          void fetchConversasEReais(activeTenantId);
        })
        .on("postgres_changes", { event: "*", schema: "public", table: "conversas", filter: `tenant_id=eq.${activeTenantId}` }, () => {
          void fetchConversasEReais(activeTenantId);
        })
        .subscribe();
    });

    return () => {
      mounted = false;
      if (channel) void supabase.removeChannel(channel);
    };
  }, [supabase]);

  const conversaSelecionada = conversas.find((c) => c.id === selecionadaId);
  const mensagensDaConversa = useMemo(() => {
    if (!conversaSelecionada) return [];
    return mensagens[conversaSelecionada.id] || [];
  }, [conversaSelecionada, mensagens]);

  const assumirConversa = async (id: string) => {
    setConversas((prev) => prev.map((c) => (c.id === id ? { ...c, estado: "humano" } : c)));
    try {
      await supabase.from("conversas").update({ estado: "humano" }).eq("id", id).eq("tenant_id", tenantId);
    } catch {
      //
    }
  };

  const devolverParaIA = async (id: string) => {
    setConversas((prev) => prev.map((c) => (c.id === id ? { ...c, estado: "ia" } : c)));
    try {
      await supabase.from("conversas").update({ estado: "ia" }).eq("id", id).eq("tenant_id", tenantId);
    } catch {
      //
    }
  };

  const handleEnviarMensagem = (event: React.FormEvent) => {
    event.preventDefault();
    if (!novoTexto.trim() || !conversaSelecionada) return;

    const texto = novoTexto.trim();
    setNovoTexto("");
    setMensagens((prev) => ({
      ...prev,
      [conversaSelecionada.id]: [
        ...(prev[conversaSelecionada.id] || []),
        {
          id: Date.now(),
          remetente: "atendente",
          texto,
          enviado_em: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ],
    }));
  };

  const renderBadge = (estado: Conversa["estado"]) => {
    if (estado === "ia") return <Badge variant="success">IA atendendo</Badge>;
    if (estado === "transbordo") return <Badge variant="warning" pulse>Transbordo</Badge>;
    return <Badge variant="purple">Humano</Badge>;
  };

  return (
    <section className="space-y-5" aria-labelledby="conversas-title">
      <div>
        <h1 id="conversas-title" className="section-heading">
          Atendimento
        </h1>
        <p className="section-subtitle">Conversas do WhatsApp, com transbordo e retomada.</p>
      </div>

      <div className="glass-card grid min-h-[562px] overflow-hidden lg:grid-cols-[236px_minmax(0,1fr)] xl:grid-cols-[236px_minmax(0,1fr)_254px]">
        <aside style={{ background: "var(--c2)", borderRight: "1px solid var(--line2)" }}>
          <div className="flex justify-between px-[15px] py-[10px] font-mono text-[8.6px] uppercase tracking-[0.15em]" style={{ borderBottom: "1px solid var(--line2)", color: "var(--mut)" }}>
            <span>Conversas</span>
            <span>{conversas.length}</span>
          </div>
          <div>
            {conversas.map((conversa) => {
              const isActive = selecionadaId === conversa.id;
              return (
                <button
                  key={conversa.id}
                  type="button"
                  onClick={() => setSelecionadaId(conversa.id)}
                  className="block w-full px-[15px] py-3 text-left transition"
                  style={{
                    background: isActive ? "var(--card)" : "transparent",
                    borderBottom: "1px solid var(--line2)",
                    borderLeft: isActive ? "3px solid var(--gold)" : "3px solid transparent",
                  }}
                >
                  <div className="flex items-center gap-2">
                    <span className="grid h-[27px] w-[27px] flex-none place-items-center rounded-full text-[10px] font-bold" style={{ background: "var(--c3)", color: "var(--ink2)" }}>
                      {conversa.contato_nome.split(" ").map((x) => x[0]).slice(0, 2).join("")}
                    </span>
                    <span className="min-w-0 flex-1 truncate text-[12.3px] font-bold">{conversa.contato_nome}</span>
                    <span className="font-mono text-[9.5px]" style={{ color: "var(--mut)" }}>{conversa.atualizado_em}</span>
                  </div>
                  <p className="ml-9 mt-1 line-clamp-2 text-[10.8px]" style={{ color: "var(--mut)" }}>
                    {conversa.ultima_mensagem}
                  </p>
                  <div className="ml-9 mt-2">{renderBadge(conversa.estado)}</div>
                </button>
              );
            })}
          </div>
        </aside>

        <main className="flex min-w-0 flex-col bg-white">
          {conversaSelecionada ? (
            <>
              <div className="flex items-center justify-between gap-3 px-5 py-[10px]" style={{ borderBottom: "1px solid var(--line2)" }}>
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="font-display text-[22px] leading-tight">{conversaSelecionada.contato_nome}</h2>
                    {renderBadge(conversaSelecionada.estado)}
                  </div>
                  <p className="text-[11.6px]" style={{ color: "var(--mut)" }}>{conversaSelecionada.telefone}</p>
                </div>
                {conversaSelecionada.estado === "humano" ? (
                  <button type="button" onClick={() => devolverParaIA(conversaSelecionada.id)} className="glass-btn glass-btn-primary">
                    Devolver para IA
                  </button>
                ) : (
                  <button type="button" onClick={() => assumirConversa(conversaSelecionada.id)} className="glass-btn glass-btn-ghost">
                    Assumir conversa
                  </button>
                )}
              </div>

              <div className="flex max-h-[462px] flex-1 flex-col gap-3 overflow-y-auto px-5 py-4">
                {mensagensDaConversa.map((mensagem) => (
                  <div key={mensagem.id} className="flex gap-3">
                    <span className="w-[35px] flex-none pt-1 font-mono text-[9.4px]" style={{ color: "var(--mut2)" }}>
                      {mensagem.enviado_em}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="mb-1 font-mono text-[8.4px] uppercase tracking-[0.13em]" style={{ color: mensagem.remetente === "atendente" ? "var(--gold)" : "var(--sage)" }}>
                        {mensagem.remetente === "atendente" ? "Atendente" : mensagem.remetente === "ia" ? "IA" : "Cliente"}
                      </div>
                      <div
                        className="rounded-[8px] px-3 py-[10px] text-[12.7px] leading-relaxed"
                        style={{
                          background: mensagem.remetente === "atendente" || mensagem.remetente === "ia" ? "var(--gold-l)" : "var(--c2)",
                          borderLeft: `2px solid ${mensagem.remetente === "atendente" || mensagem.remetente === "ia" ? "var(--gold)" : "var(--mut2)"}`,
                        }}
                      >
                        {mensagem.texto}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {conversaSelecionada.estado !== "ia" && (
                <div className="mx-5 mb-3 flex items-center gap-3 rounded-[8px] p-3" style={{ background: conversaSelecionada.estado === "transbordo" ? "var(--wine-l)" : "var(--gold-l)", border: "1px solid var(--gold-b)" }}>
                  <div className="flex-1">
                    <b className="block text-[12.6px]">{conversaSelecionada.estado === "transbordo" ? "Transbordo aberto" : "Atendimento humano ativo"}</b>
                    <small className="text-[11.2px]" style={{ color: "var(--ink2)" }}>A IA pausa enquanto a conversa estiver com a equipe.</small>
                  </div>
                </div>
              )}

              <form onSubmit={handleEnviarMensagem} className="flex gap-2 px-5 py-3" style={{ background: "var(--c2)", borderTop: "1px solid var(--line2)" }}>
                <input
                  value={novoTexto}
                  onChange={(event) => setNovoTexto(event.target.value)}
                  placeholder={conversaSelecionada.estado === "humano" ? "Digite sua resposta como atendente..." : "Assuma a conversa para responder..."}
                  disabled={conversaSelecionada.estado !== "humano"}
                  className="glass-input flex-1"
                />
                <button type="submit" disabled={conversaSelecionada.estado !== "humano"} className="glass-btn glass-btn-primary px-4" aria-label="Enviar mensagem">
                  <Send className="h-4 w-4" />
                </button>
              </form>
            </>
          ) : (
            <div className="grid flex-1 place-items-center text-sm" style={{ color: "var(--mut)" }}>
              Selecione uma conversa para visualizar
            </div>
          )}
        </main>

        <aside className="hidden flex-col xl:flex" style={{ background: "var(--c2)", borderLeft: "1px solid var(--line2)" }}>
          <div className="p-[15px]" style={{ borderBottom: "1px solid var(--line2)" }}>
            <h3 className="font-mono text-[8.4px] uppercase tracking-[0.15em]" style={{ color: "var(--mut)" }}>Lead</h3>
            <div className="mt-3 space-y-2 text-[12px]">
              <div className="flex justify-between gap-3"><span style={{ color: "var(--mut)" }}>Status</span><b>{conversaSelecionada?.estado ?? "-"}</b></div>
              <div className="flex justify-between gap-3"><span style={{ color: "var(--mut)" }}>Canal</span><b>WhatsApp</b></div>
              <div className="flex justify-between gap-3"><span style={{ color: "var(--mut)" }}>Origem</span><b>Meta</b></div>
            </div>
          </div>
          <div className="p-[15px]">
            <h3 className="font-mono text-[8.4px] uppercase tracking-[0.15em]" style={{ color: "var(--mut)" }}>Chamadas à API</h3>
            <div className="mt-3 rounded-[8px] border bg-white p-2 font-mono text-[9.6px] leading-relaxed" style={{ borderColor: "var(--line)", color: "var(--ink2)" }}>
              <span style={{ color: "var(--gold)", fontWeight: 600 }}>GET</span> /conversas/live
              <span className="mt-1 block" style={{ color: "var(--sage)" }}>200 OK · realtime ativo</span>
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}
