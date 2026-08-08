import React, { useState, useEffect, useRef } from 'react';
import { Scenario, ChatStep, ProductItem } from '../../types';
import { CHAT_SCENARIOS } from '../../data/mockData';
import { ThreadMessage } from './ThreadMessage';
import { HandoffBanner } from './HandoffBanner';
import { WebLocacionTraces } from './WebLocacionTraces';
import { Play, RotateCcw, Send, MessageSquare } from 'lucide-react';

interface ChatViewProps {
  initialScenarioId?: string;
  onShowToast: (title: string, subtitle?: string) => void;
}

interface RenderedMessage {
  id: string;
  actor: 'cli' | 'ia' | 'ag' | 'sys';
  text?: string;
  time: string;
  products?: ProductItem[];
}

export const ChatView: React.FC<ChatViewProps> = ({ initialScenarioId, onShowToast }) => {
  const [activeScenarioIdx, setActiveScenarioIdx] = useState<number>(0);
  const [messages, setMessages] = useState<RenderedMessage[]>([]);
  const [traces, setTraces] = useState<{ m: string; p: string; r: string; w?: number }[]>([]);
  const [contextFields, setContextFields] = useState<[string, string, string?][]>([]);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isTaken, setIsTaken] = useState<boolean>(false);
  const [showHandoffBanner, setShowHandoffBanner] = useState<boolean>(false);
  const [agentInput, setAgentInput] = useState<string>('');

  const threadEndRef = useRef<HTMLDivElement>(null);

  const scenario = CHAT_SCENARIOS[activeScenarioIdx];

  useEffect(() => {
    if (initialScenarioId) {
      const idx = CHAT_SCENARIOS.findIndex((s) => s.id === initialScenarioId);
      if (idx !== -1) {
        setActiveScenarioIdx(idx);
      }
    }
  }, [initialScenarioId]);

  useEffect(() => {
    loadScenario();
  }, [activeScenarioIdx]);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadScenario = () => {
    const s = CHAT_SCENARIOS[activeScenarioIdx];
    setMessages([]);
    setTraces([]);
    setContextFields(s.ctx.map(([l, v, k]) => [l, v, k]));
    setIsPlaying(false);
    setIsTaken(false);
    setShowHandoffBanner(false);
    setAgentInput('');
  };

  const runSimulation = async () => {
    if (isPlaying) return;
    setIsPlaying(true);

    const s = CHAT_SCENARIOS[activeScenarioIdx];
    let currentTime = 21 * 60 + 48; // 21:48

    const getTimeStr = (addMins = 0) => {
      currentTime += addMins;
      const h = Math.floor(currentTime / 60) % 24;
      const m = currentTime % 60;
      return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
    };

    for (const st of s.steps) {
      await new Promise((r) => setTimeout(r, 600));

      if (st.k === 'in') {
        setMessages((prev) => [
          ...prev,
          { id: Math.random().toString(), actor: 'cli', text: st.t, time: getTimeStr(1) },
        ]);
      } else if (st.k === 'ia') {
        setMessages((prev) => [
          ...prev,
          { id: Math.random().toString(), actor: 'ia', text: st.t, time: getTimeStr(0), products: st.prods },
        ]);
      } else if (st.k === 'ag') {
        setMessages((prev) => [
          ...prev,
          { id: Math.random().toString(), actor: 'ag', text: st.t, time: getTimeStr(1) },
        ]);
      } else if (st.k === 'sys') {
        setMessages((prev) => [
          ...prev,
          { id: Math.random().toString(), actor: 'sys', text: st.t, time: getTimeStr(0) },
        ]);
      } else if (st.k === 'api' && st.m && st.p && st.r) {
        setTraces((prev) => [...prev, { m: st.m!, p: st.p!, r: st.r!, w: st.w }]);
      } else if (st.k === 'ctx' && st.key && st.v) {
        setContextFields((prev) =>
          prev.map(([l, v, k]) => (k === st.key ? [l, st.v!, k] : [l, v, k]))
        );
      } else if (st.k === 'ho') {
        setShowHandoffBanner(true);
        setMessages((prev) => [
          ...prev,
          {
            id: Math.random().toString(),
            actor: 'sys',
            text: 'Transbordo aberto · IA pausada · aguardando atendente humano',
            time: getTimeStr(0),
          },
        ]);
      }
    }

    setIsPlaying(false);
  };

  const handleTakeover = async () => {
    setIsTaken(true);
    setMessages((prev) => [
      ...prev,
      { id: Math.random().toString(), actor: 'sys', text: 'Juliana assumiu o controle · IA pausada', time: '21:55' },
    ]);

    const s = CHAT_SCENARIOS[activeScenarioIdx];
    if (s.after) {
      for (const st of s.after) {
        await new Promise((r) => setTimeout(r, 600));
        if (st.k === 'ag') {
          setMessages((prev) => [
            ...prev,
            { id: Math.random().toString(), actor: 'ag', text: st.t, time: '21:56' },
          ]);
        } else if (st.k === 'in') {
          setMessages((prev) => [
            ...prev,
            { id: Math.random().toString(), actor: 'cli', text: st.t, time: '21:57' },
          ]);
        }
      }
    }
  };

  const handleReturnToAI = () => {
    setIsTaken(false);
    setShowHandoffBanner(false);
    setMessages((prev) => [
      ...prev,
      {
        id: Math.random().toString(),
        actor: 'sys',
        text: 'Conversa devolvida para a automação · IA responderá à próxima mensagem',
        time: '21:58',
      },
    ]);
    onShowToast('Automação Retomada', 'A IA volta a responder esta conversa no WhatsApp.');
  };

  const handleSendAgentMessage = () => {
    if (!agentInput.trim()) return;
    setMessages((prev) => [
      ...prev,
      { id: Math.random().toString(), actor: 'ag', text: agentInput, time: '21:59' },
    ]);
    setAgentInput('');
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden animate-fade-in flex flex-col lg:flex-row h-[700px]">
      {/* Left Sidebar: Conversations Inbox */}
      <div className="w-full lg:w-60 border-r border-slate-200 bg-[#FAF7F2] flex flex-col">
        <div className="p-3 border-b border-slate-200 font-mono text-[9px] uppercase tracking-widest text-slate-400 font-bold flex justify-between">
          <span>Conversas WhatsApp</span>
          <span className="bg-[#7B2233] text-white px-1.5 py-0.2 rounded-full font-bold">
            {CHAT_SCENARIOS.length}
          </span>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1 p-2">
          {CHAT_SCENARIOS.map((s, idx) => {
            const isSelected = idx === activeScenarioIdx;
            return (
              <div
                key={s.id}
                onClick={() => {
                  if (!isPlaying) setActiveScenarioIdx(idx);
                }}
                className={`p-3 rounded-xl cursor-pointer transition-all border text-xs relative ${
                  isSelected
                    ? 'bg-white border-[#0E4A7B] shadow-2xs font-semibold'
                    : 'border-transparent hover:bg-slate-100/80 text-slate-600'
                }`}
              >
                {isSelected && (
                  <span className="absolute left-0 top-2 bottom-2 w-1 bg-[#0E4A7B] rounded-r"></span>
                )}
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-6 h-6 rounded-full bg-[#EFE9DE] text-[#1F1B17] font-bold text-[10px] grid place-items-center">
                    {s.c.i}
                  </div>
                  <b className="text-slate-900 truncate flex-1">{s.c.n}</b>
                </div>
                <p className="text-[11px] text-slate-500 line-clamp-2 pl-8">{s.pv}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Middle Area: Chat Header, Thread & Input */}
      <div className="flex-1 flex flex-col bg-white min-w-0">
        {/* Chat Control Bar */}
        <div className="p-3.5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-[#FAF7F2]">
          <div>
            <h3 className="font-semibold text-xs text-slate-900">{scenario.t}</h3>
            <span className="text-[11px] text-slate-500 block font-mono">{scenario.h}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadScenario}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Reiniciar
            </button>
            <button
              onClick={runSimulation}
              disabled={isPlaying}
              className="px-3 py-1.5 bg-[#0E4A7B] hover:bg-[#072F53] disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs"
            >
              <Play className="w-3.5 h-3.5 fill-current" /> {isPlaying ? 'Rodando...' : 'Rodar Conversa'}
            </button>
          </div>
        </div>

        {/* Chat Messages Thread */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400 space-y-2">
              <MessageSquare className="w-8 h-8 text-slate-300" />
              <p className="text-xs">Clique em <b>“Rodar conversa”</b> para simular o atendimento em tempo real.</p>
            </div>
          ) : (
            messages.map((m) => (
              <ThreadMessage
                key={m.id}
                actor={m.actor}
                text={m.text}
                time={m.time}
                products={m.products}
              />
            ))
          )}
          <div ref={threadEndRef} />
        </div>

        {/* Handoff Banner */}
        <HandoffBanner
          isOpen={showHandoffBanner}
          isTaken={isTaken}
          onTakeover={handleTakeover}
          onReturnToAI={handleReturnToAI}
        />

        {/* Input Composer */}
        <div className="p-3 border-t border-slate-200 bg-[#FAF7F2] flex gap-2">
          <input
            type="text"
            value={agentInput}
            onChange={(e) => setAgentInput(e.target.value)}
            disabled={!isTaken}
            placeholder={isTaken ? 'Responder como Juliana...' : 'Assuma a conversa para responder...'}
            className="flex-1 bg-white border border-slate-200 rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-[#0E4A7B] disabled:bg-slate-100 disabled:opacity-60"
            onKeyDown={(e) => e.key === 'Enter' && handleSendAgentMessage()}
          />
          <button
            onClick={handleSendAgentMessage}
            disabled={!isTaken || !agentInput.trim()}
            className="bg-[#0E4A7B] hover:bg-[#072F53] disabled:opacity-50 text-white px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Send className="w-3.5 h-3.5" /> Enviar
          </button>
        </div>
      </div>

      {/* Right Sidebar: WebLocação API Traces */}
      <WebLocacionTraces contextFields={contextFields} traces={traces} />
    </div>
  );
};
