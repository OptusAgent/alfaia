"use client";

import { useState } from "react";
import { Cpu, Lock, ShieldAlert, CheckCircle2, RefreshCw, Zap } from "lucide-react";

interface AutomacaoItem {
  chave: string;
  nome: string;
  descricao: string;
  ativo: bool;
  pode_desligar: bool;
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
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-neutral-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 flex items-center gap-2.5">
            <Cpu className="h-7 w-7 text-brand-600" />
            Gestão de Automações & Toggles
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Ligue ou desligue rotinas individualmente sem afetar as demais (PRD §16, S-32).
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
            <option value="operador">Operador (Autorizado)</option>
            <option value="dono">Dono (Autorizado)</option>
            <option value="atendente">Atendente (Bloqueado)</option>
          </select>
        </div>
      </div>

      {/* Alertas */}
      {mensagemSucesso && (
        <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl flex items-center gap-3 text-emerald-800 text-xs font-semibold">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
          {mensagemSucesso}
        </div>
      )}

      {erro && (
        <div className="bg-red-50 border border-red-200 p-4 rounded-xl flex items-center gap-3 text-red-800 text-xs font-semibold">
          <ShieldAlert className="h-5 w-5 text-red-600 shrink-0" />
          {erro}
        </div>
      )}

      {/* Lista das 8 Automações (AC 1, AC 2) */}
      <div className="space-y-3">
        {automacoes.map((item) => (
          <div
            key={item.chave}
            className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
              item.ativo ? "bg-white border-neutral-200 shadow-2xs" : "bg-neutral-50 border-neutral-200 opacity-75"
            }`}
          >
            <div className="space-y-1 max-w-xl">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-neutral-900">{item.nome}</span>
                <span className="font-mono text-[10px] bg-neutral-100 text-neutral-600 px-2 py-0.5 rounded-md">
                  {item.chave}
                </span>

                {!item.pode_desligar && (
                  <span className="bg-amber-100 text-amber-900 text-[10px] font-extrabold px-2 py-0.5 rounded-full flex items-center gap-1">
                    <Lock className="h-3 w-3 text-amber-700" /> Estrutural Obrigatória (P5/P8)
                  </span>
                )}
              </div>
              <p className="text-xs text-neutral-500">{item.descricao}</p>
            </div>

            {/* Toggle Switch */}
            <div className="flex items-center gap-3">
              <span className={`text-xs font-semibold ${item.ativo ? "text-emerald-700" : "text-neutral-400"}`}>
                {item.ativo ? "Ativa" : "Desativada"}
              </span>

              <button
                onClick={() => handleToggle(item.chave, !item.ativo)}
                disabled={!item.pode_desligar || userRole === "atendente"}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-hidden ${
                  item.ativo ? "bg-brand-600" : "bg-neutral-300"
                } ${(!item.pode_desligar || userRole === "atendente") ? "cursor-not-allowed opacity-60" : ""}`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    item.ativo ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
