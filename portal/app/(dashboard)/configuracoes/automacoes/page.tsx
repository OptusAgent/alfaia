"use client";

import { useState } from "react";
import { Badge } from "@/app/components/ui/Badge";
import { Cpu, Lock, ShieldAlert, CheckCircle2 } from "lucide-react";

interface AutomacaoItem {
  chave: string;
  nome: string;
  descricao: string;
  ativo: boolean;
  pode_desligar: boolean;
}

export default function AutomacoesPage() {
  const [userRole, setUserRole] = useState<string>("operador");
  const [erro, setErro] = useState<string | null>(null);
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);

  const [automacoes, setAutomacoes] = useState<AutomacaoItem[]>([
    { chave: "atendimento", nome: "Atendimento IA & Qualificação", descricao: "Responde mensagens novas, qualifica o lead e agenda eventos.", ativo: true, pode_desligar: true },
    { chave: "identificacao", nome: "Identificação de Contato & Lead", descricao: "Identifica, cria ou retoma o lead (Estrutural P5/P8 - Não desligável).", ativo: true, pode_desligar: false },
    { chave: "disponibilidade", nome: "Consulta de Disponibilidade", descricao: "Consulta estoque e peças na WebLocação.", ativo: true, pode_desligar: true },
    { chave: "agendamento", nome: "Agendamento de Provas", descricao: "Reserva horários e slots na agenda do estabelecimento.", ativo: true, pode_desligar: true },
    { chave: "followup", nome: "Worker de Follow-up", descricao: "Dispara mensagens automáticas após janela de silêncio.", ativo: true, pode_desligar: true },
    { chave: "descarte", nome: "Descarte & Retenção de Lead", descricao: "Arquiva leads desengajados sem apagar contatos (P5).", ativo: true, pode_desligar: true },
    { chave: "transbordo", nome: "Transbordo Humano", descricao: "Pausa a IA e transfere atendimento a um operador.", ativo: true, pode_desligar: true },
    { chave: "campanha", nome: "Engine de Campanhas & Disparo", descricao: "Dispara campanhas em lote com proteção anti-ban (K1-K8).", ativo: true, pode_desligar: true },
  ]);

  const handleToggle = (chave: string, novoEstado: boolean) => {
    setErro(null);
    setMensagemSucesso(null);

    // AC 4: Guard de permissão
    if (userRole === "atendente") {
      setErro("Permissão negada. O perfil 'atendente' não pode alterar automações (apenas 'dono' ou 'operador').");
      return;
    }

    // AC 2: Trava Estrutural
    if (chave === "identificacao" && !novoEstado) {
      setErro("A automação 'identificacao' é estrutural para as regras P5 e P8 da plataforma e não pode ser desligada.");
      return;
    }

    setAutomacoes((prev) =>
      prev.map((item) => (item.chave === chave ? { ...item, ativo: novoEstado } : item))
    );

    setMensagemSucesso(`Automação '${chave}' ${novoEstado ? "ativada" : "desativada"} com sucesso!`);
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
            <Cpu className="h-7 w-7" style={{ color: "var(--accent-primary)" }} />
            Gestão de Automações & Toggles
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Ligue ou desligue rotinas individualmente sem afetar as demais.
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

      {/* Alerts */}
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
          {mensagemSucesso}
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

      {/* Automation List */}
      <div className="space-y-3">
        {automacoes.map((item) => (
          <div
            key={item.chave}
            className="glass-card p-4 flex items-center justify-between transition-all"
            style={{
              opacity: item.ativo ? 1 : 0.6,
            }}
          >
            <div className="space-y-1 max-w-xl">
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className="font-bold text-sm"
                  style={{ color: "var(--text-primary)" }}
                >
                  {item.nome}
                </span>
                <span
                  className="font-mono text-[10px] px-2 py-0.5 rounded-md"
                  style={{
                    background: "rgba(255, 255, 255, 0.06)",
                    color: "var(--text-muted)",
                  }}
                >
                  {item.chave}
                </span>

                {!item.pode_desligar && (
                  <Badge variant="warning" icon={<Lock className="h-3 w-3" />}>
                    Estrutural Obrigatória
                  </Badge>
                )}
              </div>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                {item.descricao}
              </p>
            </div>

            {/* Toggle Switch */}
            <div className="flex items-center gap-3">
              <span
                className="text-xs font-semibold"
                style={{
                  color: item.ativo ? "var(--accent-primary)" : "var(--text-muted)",
                }}
              >
                {item.ativo ? "Ativa" : "Desativada"}
              </span>

              <button
                onClick={() => handleToggle(item.chave, !item.ativo)}
                disabled={!item.pode_desligar || userRole === "atendente"}
                className="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-hidden disabled:cursor-not-allowed disabled:opacity-60"
                style={{
                  backgroundColor: item.ativo
                    ? "var(--accent-primary)"
                    : "rgba(255, 255, 255, 0.1)",
                }}
              >
                <span
                  className="pointer-events-none inline-block h-5 w-5 transform rounded-full shadow-lg ring-0 transition duration-200 ease-in-out"
                  style={{
                    backgroundColor: "var(--text-primary)",
                    transform: item.ativo ? "translateX(1.25rem)" : "translateX(0)",
                  }}
                />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
