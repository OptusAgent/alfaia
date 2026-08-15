"use client";

import { useState } from "react";
import { Bot, Lock, Save, ShieldAlert, Sparkles, Sliders, CheckCircle2, Key, Cpu } from "lucide-react";

export default function IaConfigPage() {
  const [userRole, setUserRole] = useState<string>("operador");
  const [provedor, setProvedor] = useState<string>("openrouter");
  const [openrouterKey, setOpenrouterKey] = useState<string>("");
  const [openaiKey, setOpenaiKey] = useState<string>("");
  const [personaNome, setPersonaNome] = useState<string>("Atendente da Alfaia");
  const [promptSistema, setPromptSistema] = useState<string>(
    "Você é a atendente virtual da Alfaia Alta Costura. Seu tom é elegante, acolhedor e atencioso. Auxilie a cliente com dúvidas sobre vestidos sob medida, provas e locações."
  );
  const [modelo, setModelo] = useState<string>("deepseek/deepseek-r1-distill-llama-70b");
  const [temperatura, setTemperatura] = useState<number>(0.3);
  const [janelaRetomadaDias, setJanelaRetomadaDias] = useState<number>(7);
  const [janelaSilencioHoras, setJanelaSilencioHoras] = useState<number>(24);
  const [maxTentativasFollowup, setMaxTentativasFollowup] = useState<number>(3);

  const [salvando, setSalvando] = useState(false);
  const [mensagemSucesso, setMensagemSucesso] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const handleSalvar = () => {
    setErro(null);
    setMensagemSucesso(false);

    if (userRole !== "operador") {
      setErro("Permissão negada. Apenas o perfil 'operador' pode salvar alterações no prompt e persona.");
      return;
    }

    if (janelaRetomadaDias < 1 || janelaRetomadaDias > 90) {
      setErro("A Janela de Retomada deve estar entre 1 e 90 dias.");
      return;
    }

    setSalvando(true);
    setTimeout(() => {
      setSalvando(false);
      setMensagemSucesso(true);
    }, 500);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-neutral-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 flex items-center gap-2.5">
            <Bot className="h-7 w-7 text-brand-600" />
            Configuração da IA & Persona
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Personalize o provedor de IA, chaves de API, identidade da persona e parâmetros de atendimento.
          </p>
        </div>

        {/* Role Selector para teste de permissão */}
        <div className="flex items-center gap-2 bg-neutral-100 p-1.5 rounded-lg border text-xs">
          <span className="font-semibold text-neutral-600">Simular Papel:</span>
          <select
            value={userRole}
            onChange={(e) => setUserRole(e.target.value)}
            className="bg-white border rounded-md px-2 py-1 font-bold text-neutral-800"
          >
            <option value="operador">Operador (Acesso Total)</option>
            <option value="dono">Dono (Bloqueado)</option>
            <option value="atendente">Atendente (Bloqueado)</option>
          </select>
        </div>
      </div>

      {/* Alerta de Sucesso ou Erro */}
      {mensagemSucesso && (
        <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl flex items-center gap-3 text-emerald-800 text-xs font-semibold">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
          Configurações da IA salvas com sucesso! O Bloco 2 de Regras Invioláveis permaneceu intocado.
        </div>
      )}

      {erro && (
        <div className="bg-red-50 border border-red-200 p-4 rounded-xl flex items-center gap-3 text-red-800 text-xs font-semibold">
          <ShieldAlert className="h-5 w-5 text-red-600 shrink-0" />
          {erro}
        </div>
      )}

      {/* Bloco 0: Provedor & Credenciais de IA */}
      <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-2xs space-y-4">
        <h2 className="text-sm font-bold text-neutral-900 flex items-center gap-2 border-b pb-2">
          <Cpu className="h-4 w-4 text-brand-600" /> Provedor de LLM & Credenciais de Teste
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-semibold text-neutral-700">Provedor Ativo:</label>
            <select
              value={provedor}
              onChange={(e) => setProvedor(e.target.value)}
              className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300 bg-white font-semibold"
            >
              <option value="openrouter">OpenRouter (Testes Atuais / Multi-modelo)</option>
              <option value="openai">OpenAI (Oficial / Estrutura Futura)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-neutral-700">Modelo Selecionado:</label>
            <select
              value={modelo}
              onChange={(e) => setModelo(e.target.value)}
              className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300 bg-white font-mono"
            >
              {provedor === "openrouter" ? (
                <>
                  <option value="deepseek/deepseek-r1-distill-llama-70b">DeepSeek R1 Distill Llama 70B (OpenRouter)</option>
                  <option value="meta-llama/llama-3.3-70b-instruct">Llama 3.3 70B Instruct (OpenRouter)</option>
                  <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet (OpenRouter)</option>
                </>
              ) : (
                <>
                  <option value="gpt-4o-mini">GPT-4o-mini (OpenAI Oficial)</option>
                  <option value="gpt-4o">GPT-4o (OpenAI Oficial)</option>
                </>
              )}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div>
            <label className="text-xs font-semibold text-neutral-700 flex items-center gap-1">
              <Key className="h-3.5 w-3.5 text-neutral-500" /> Chave OpenRouter (Ativa nos testes):
            </label>
            <input
              type="password"
              placeholder="sk-or-v1-..."
              value={openrouterKey}
              onChange={(e) => setOpenrouterKey(e.target.value)}
              className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300 font-mono"
            />
            <span className="text-[10px] text-neutral-400">Extraia em openrouter.ai {"->"} Keys</span>
          </div>

          <div>
            <label className="text-xs font-semibold text-neutral-700 flex items-center gap-1">
              <Key className="h-3.5 w-3.5 text-neutral-500" /> Chave OpenAI (Estrutura pronta):
            </label>
            <input
              type="password"
              placeholder="sk-proj-..."
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300 font-mono"
            />
            <span className="text-[10px] text-neutral-400">Extraia em platform.openai.com {"->"} API Keys</span>
          </div>
        </div>
      </div>

      {/* Bloco 1: Identidade & Persona (EDITÁVEL) */}
      <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-2xs space-y-4">
        <h2 className="text-sm font-bold text-neutral-900 flex items-center gap-2 border-b pb-2">
          <Sparkles className="h-4 w-4 text-brand-600" /> Bloco 1: Identidade & Persona da IA (Editável por Operador)
        </h2>

        <div>
          <label className="text-xs font-semibold text-neutral-700">Nome da Persona:</label>
          <input
            type="text"
            value={personaNome}
            onChange={(e) => setPersonaNome(e.target.value)}
            className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300 focus:outline-hidden focus:border-brand-500"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-neutral-700">Prompt do Sistema (Tom e Personalidade):</label>
          <textarea
            rows={4}
            value={promptSistema}
            onChange={(e) => setPromptSistema(e.target.value)}
            className="w-full mt-1 p-3 text-xs rounded-lg border border-neutral-300 focus:outline-hidden focus:border-brand-500 font-mono leading-relaxed"
          />
        </div>
      </div>

      {/* Bloco 2: Regras Invioláveis (TRAVADO / NÃO EDITÁVEL - AC 1) */}
      <div className="bg-amber-50/50 p-6 rounded-xl border border-amber-200/80 space-y-3">
        <div className="flex items-center justify-between border-b border-amber-200/60 pb-2">
          <h2 className="text-sm font-bold text-amber-950 flex items-center gap-2">
            <Lock className="h-4 w-4 text-amber-600" /> Bloco 2: Regras Invioláveis do Sistema (Não Editável)
          </h2>
          <span className="bg-amber-200 text-amber-900 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider flex items-center gap-1">
            <Lock className="h-3 w-3" /> Imutável
          </span>
        </div>
        <p className="text-xs text-amber-800 leading-relaxed">
          Estas 4 regras são gravadas em código e injetadas automaticamente no prompt final de todos os atendimentos para proteger o tenant:
        </p>
        <ul className="text-xs text-amber-900 space-y-1.5 list-disc list-inside font-medium bg-white/70 p-3 rounded-lg border border-amber-200/50">
          <li><strong>Regra R1 (Fidelidade ao Catálogo)</strong>: Nunca inventar preços, modelos ou estoques fora da base.</li>
          <li><strong>Regra R2 (Sem Menus Numéricos)</strong>: Atendimento 100% conversacional em linguagem natural.</li>
          <li><strong>Regra R3 (Proteção de Dados LGPD)</strong>: Nunca solicitar CPF, RG ou dados sensíveis no chat.</li>
          <li><strong>Regra R4 (Transbordo em Falha)</strong>: Acionar atendimento humano imediatamente em caso de insatisfação.</li>
        </ul>
      </div>

      {/* Bloco 3: Parâmetros de Atendimento */}
      <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-2xs space-y-4">
        <h2 className="text-sm font-bold text-neutral-900 flex items-center gap-2 border-b pb-2">
          <Sliders className="h-4 w-4 text-brand-600" /> Parâmetros de Atendimento & Follow-Up
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="text-xs font-semibold text-neutral-700">Janela de Retomada (Dias):</label>
            <input
              type="number"
              min={1}
              max={90}
              value={janelaRetomadaDias}
              onChange={(e) => setJanelaRetomadaDias(Number(e.target.value))}
              className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300"
            />
            <span className="text-[10px] text-neutral-400">Faixa: 1 a 90 dias</span>
          </div>

          <div>
            <label className="text-xs font-semibold text-neutral-700">Janela de Silêncio (Horas):</label>
            <input
              type="number"
              value={janelaSilencioHoras}
              onChange={(e) => setJanelaSilencioHoras(Number(e.target.value))}
              className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300"
            />
            <span className="text-[10px] text-neutral-400">Padrão: 24 horas</span>
          </div>

          <div>
            <label className="text-xs font-semibold text-neutral-700">Temperatura (Criatividade):</label>
            <input
              type="number"
              step={0.1}
              min={0}
              max={1}
              value={temperatura}
              onChange={(e) => setTemperatura(Number(e.target.value))}
              className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300"
            />
            <span className="text-[10px] text-neutral-400">Faixa: 0.0 a 1.0</span>
          </div>
        </div>
      </div>

      {/* Botão de Salvar */}
      <div className="flex justify-end pt-2">
        <button
          onClick={handleSalvar}
          disabled={salvando}
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-brand-600 text-white text-xs font-bold hover:bg-brand-700 transition"
        >
          <Save className="h-4 w-4" />
          {salvando ? "Salvando..." : "Salvar Configurações da IA"}
        </button>
      </div>
    </div>
  );
}
