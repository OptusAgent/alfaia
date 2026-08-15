"use client";

import { useState } from "react";
import { Badge } from "@/app/components/ui/Badge";
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
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div
        className="flex items-center justify-between pb-4"
        style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.06)" }}
      >
        <div>
          <h1
            className="text-2xl font-bold font-display flex items-center gap-2.5"
            style={{ color: "var(--text-primary)" }}
          >
            <Bot className="h-7 w-7" style={{ color: "var(--accent-primary)" }} />
            Configuração da IA & Persona
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Personalize o provedor de IA, chaves de API, identidade da persona e parâmetros de atendimento.
          </p>
        </div>

        {/* Role Selector */}
        <div
          className="flex items-center gap-2 p-1.5 rounded-lg text-xs"
          style={{
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.06)",
          }}
        >
          <span className="font-semibold" style={{ color: "var(--text-muted)" }}>
            Papel:
          </span>
          <select
            value={userRole}
            onChange={(e) => setUserRole(e.target.value)}
            className="glass-select py-1 text-xs"
            style={{ width: "auto" }}
          >
            <option value="operador">Operador</option>
            <option value="dono">Dono</option>
            <option value="atendente">Atendente</option>
          </select>
        </div>
      </div>

      {/* Success / Error Alerts */}
      {mensagemSucesso && (
        <div
          className="p-4 rounded-xl flex items-center gap-3 text-xs font-semibold"
          style={{
            background: "var(--accent-primary-muted)",
            color: "var(--accent-primary)",
            border: "1px solid rgba(16, 185, 129, 0.2)",
          }}
        >
          <CheckCircle2 className="h-5 w-5 shrink-0" />
          Configurações da IA salvas com sucesso! O Bloco 2 de Regras Invioláveis permaneceu intocado.
        </div>
      )}

      {erro && (
        <div
          className="p-4 rounded-xl flex items-center gap-3 text-xs font-semibold"
          style={{
            background: "var(--accent-coral-muted)",
            color: "var(--accent-coral)",
            border: "1px solid rgba(232, 76, 94, 0.2)",
          }}
        >
          <ShieldAlert className="h-5 w-5 shrink-0" />
          {erro}
        </div>
      )}

      {/* Block 0: LLM Provider & Credentials */}
      <div className="glass-card p-6 space-y-4">
        <h2
          className="text-sm font-bold flex items-center gap-2 pb-2"
          style={{
            color: "var(--text-primary)",
            borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
          }}
        >
          <Cpu className="h-4 w-4" style={{ color: "var(--accent-primary)" }} />
          Provedor de LLM & Credenciais
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
              Provedor Ativo:
            </label>
            <select
              value={provedor}
              onChange={(e) => setProvedor(e.target.value)}
              className="glass-select mt-1 font-semibold"
            >
              <option value="openrouter">OpenRouter (Multi-modelo)</option>
              <option value="openai">OpenAI (Oficial)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
              Modelo Selecionado:
            </label>
            <select
              value={modelo}
              onChange={(e) => setModelo(e.target.value)}
              className="glass-select mt-1 font-mono"
            >
              {provedor === "openrouter" ? (
                <>
                  <option value="deepseek/deepseek-r1-distill-llama-70b">DeepSeek R1 Distill 70B</option>
                  <option value="meta-llama/llama-3.3-70b-instruct">Llama 3.3 70B Instruct</option>
                  <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                </>
              ) : (
                <>
                  <option value="gpt-4o-mini">GPT-4o-mini</option>
                  <option value="gpt-4o">GPT-4o</option>
                </>
              )}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div>
            <label
              className="text-xs font-semibold flex items-center gap-1"
              style={{ color: "var(--text-muted)" }}
            >
              <Key className="h-3.5 w-3.5" /> Chave OpenRouter:
            </label>
            <input
              type="password"
              placeholder="sk-or-v1-..."
              value={openrouterKey}
              onChange={(e) => setOpenrouterKey(e.target.value)}
              className="glass-input mt-1 font-mono text-xs"
            />
            <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
              Extraia em openrouter.ai → Keys
            </span>
          </div>

          <div>
            <label
              className="text-xs font-semibold flex items-center gap-1"
              style={{ color: "var(--text-muted)" }}
            >
              <Key className="h-3.5 w-3.5" /> Chave OpenAI:
            </label>
            <input
              type="password"
              placeholder="sk-proj-..."
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              className="glass-input mt-1 font-mono text-xs"
            />
            <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
              Extraia em platform.openai.com → API Keys
            </span>
          </div>
        </div>
      </div>

      {/* Block 1: Persona (Editable) */}
      <div className="glass-card p-6 space-y-4">
        <h2
          className="text-sm font-bold flex items-center gap-2 pb-2"
          style={{
            color: "var(--text-primary)",
            borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
          }}
        >
          <Sparkles className="h-4 w-4" style={{ color: "var(--accent-primary)" }} />
          Bloco 1: Identidade & Persona da IA
        </h2>

        <div>
          <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
            Nome da Persona:
          </label>
          <input
            type="text"
            value={personaNome}
            onChange={(e) => setPersonaNome(e.target.value)}
            className="glass-input mt-1 text-xs"
          />
        </div>

        <div>
          <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
            Prompt do Sistema (Tom e Personalidade):
          </label>
          <textarea
            rows={4}
            value={promptSistema}
            onChange={(e) => setPromptSistema(e.target.value)}
            className="glass-input mt-1 text-xs font-mono leading-relaxed resize-y"
          />
        </div>
      </div>

      {/* Block 2: Inviolable Rules (Locked) */}
      <div
        className="p-6 rounded-xl space-y-3"
        style={{
          background: "var(--accent-amber-muted)",
          border: "1px solid var(--accent-amber-border)",
        }}
      >
        <div
          className="flex items-center justify-between pb-2"
          style={{ borderBottom: "1px solid rgba(245, 158, 11, 0.15)" }}
        >
          <h2
            className="text-sm font-bold flex items-center gap-2"
            style={{ color: "var(--accent-amber)" }}
          >
            <Lock className="h-4 w-4" />
            Bloco 2: Regras Invioláveis do Sistema
          </h2>
          <Badge variant="warning" icon={<Lock className="h-3 w-3" />}>
            Imutável
          </Badge>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          Estas 4 regras são gravadas em código e injetadas automaticamente no prompt final:
        </p>
        <ul
          className="text-xs space-y-1.5 list-disc list-inside font-medium p-3 rounded-lg"
          style={{
            background: "rgba(0, 0, 0, 0.15)",
            color: "var(--text-secondary)",
            border: "1px solid rgba(245, 158, 11, 0.1)",
          }}
        >
          <li><strong style={{ color: "var(--accent-amber)" }}>R1 (Fidelidade ao Catálogo)</strong>: Nunca inventar preços, modelos ou estoques fora da base.</li>
          <li><strong style={{ color: "var(--accent-amber)" }}>R2 (Sem Menus Numéricos)</strong>: Atendimento 100% conversacional em linguagem natural.</li>
          <li><strong style={{ color: "var(--accent-amber)" }}>R3 (LGPD)</strong>: Nunca solicitar CPF, RG ou dados sensíveis no chat.</li>
          <li><strong style={{ color: "var(--accent-amber)" }}>R4 (Transbordo)</strong>: Acionar atendimento humano em caso de insatisfação.</li>
        </ul>
      </div>

      {/* Block 3: Parameters */}
      <div className="glass-card p-6 space-y-4">
        <h2
          className="text-sm font-bold flex items-center gap-2 pb-2"
          style={{
            color: "var(--text-primary)",
            borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
          }}
        >
          <Sliders className="h-4 w-4" style={{ color: "var(--accent-primary)" }} />
          Parâmetros de Atendimento & Follow-Up
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
              Janela de Retomada (Dias):
            </label>
            <input
              type="number"
              min={1}
              max={90}
              value={janelaRetomadaDias}
              onChange={(e) => setJanelaRetomadaDias(Number(e.target.value))}
              className="glass-input mt-1 text-xs"
            />
            <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>Faixa: 1 a 90 dias</span>
          </div>

          <div>
            <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
              Janela de Silêncio (Horas):
            </label>
            <input
              type="number"
              value={janelaSilencioHoras}
              onChange={(e) => setJanelaSilencioHoras(Number(e.target.value))}
              className="glass-input mt-1 text-xs"
            />
            <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>Padrão: 24 horas</span>
          </div>

          <div>
            <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
              Temperatura (Criatividade):
            </label>
            <input
              type="number"
              step={0.1}
              min={0}
              max={1}
              value={temperatura}
              onChange={(e) => setTemperatura(Number(e.target.value))}
              className="glass-input mt-1 text-xs"
            />
            <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>Faixa: 0.0 a 1.0</span>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-2">
        <button
          onClick={handleSalvar}
          disabled={salvando}
          className="glass-btn glass-btn-primary"
        >
          <Save className="h-4 w-4" />
          {salvando ? "Salvando..." : "Salvar Configurações da IA"}
        </button>
      </div>
    </div>
  );
}
