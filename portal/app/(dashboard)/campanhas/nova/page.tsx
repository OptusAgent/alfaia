"use client";

import { useState } from "react";
import { Megaphone, Users, Eye, FileText, CheckCircle2, ArrowRight, ShieldCheck } from "lucide-react";

interface AmostraItem {
  id: string;
  nome: string;
  telefone: string;
  tags: string[];
}

export default function NovaCampanhaPage() {
  const [passo, setPasso] = useState<number>(1);
  const [nomeCampanha, setNomeCampanha] = useState<string>("Campanha Noivas Primavera 2026");
  const [tipoEvento, setTipoEvento] = useState<string>("noiva");
  const [statusLead, setStatusLead] = useState<string>("todos");

  // State da prévia
  const [carregandoPrevia, setCarregandoPrevia] = useState(false);
  const [totalElegiveis] = useState<number>(142);
  const [optoutExcluidos] = useState<number>(18);
  const [amostra] = useState<AmostraItem[]>([
    { id: "c_1", nome: "Mariana Souza", telefone: "5585999887766", tags: ["noiva", "outubro_2026"] },
    { id: "c_2", nome: "Fernanda Silva", telefone: "5585988776655", tags: ["noiva", "vestido_sereia"] },
    { id: "c_3", nome: "Juliana Paes", telefone: "5585977665544", tags: ["noiva", "madrinha"] },
  ]);

  const [salvando, setSalvando] = useState(false);
  const [sucesso, setSucesso] = useState(false);

  const handleCarregarPrevia = () => {
    setCarregandoPrevia(true);
    setTimeout(() => {
      setCarregandoPrevia(false);
      setPasso(2);
    }, 400);
  };

  const handleSalvarRascunho = () => {
    setSalvando(true);
    setTimeout(() => {
      setSalvando(false);
      setSucesso(true);
    }, 500);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="border-b border-neutral-200 pb-4">
        <h1 className="text-2xl font-bold text-neutral-900 flex items-center gap-2.5">
          <Megaphone className="h-7 w-7 text-brand-600" />
          Nova Campanha de Reengajamento
        </h1>
        <p className="text-sm text-neutral-500 mt-1">
          Defina o público alvo, confira a prévia de contatos elegíveis e configure sua mensagem.
        </p>
      </div>

      {/* Stepper Header */}
      <div className="flex items-center justify-between bg-neutral-50 p-3.5 rounded-xl border border-neutral-200 text-xs font-semibold">
        <div className={`flex items-center gap-2 ${passo >= 1 ? "text-brand-700 font-bold" : "text-neutral-400"}`}>
          <span className="w-5 h-5 rounded-full bg-brand-100 flex items-center justify-center text-[10px]">1</span>
          Segmentação
        </div>
        <ArrowRight className="h-3.5 w-3.5 text-neutral-400" />
        <div className={`flex items-center gap-2 ${passo >= 2 ? "text-brand-700 font-bold" : "text-neutral-400"}`}>
          <span className="w-5 h-5 rounded-full bg-brand-100 flex items-center justify-center text-[10px]">2</span>
          Prévia & Amostra
        </div>
        <ArrowRight className="h-3.5 w-3.5 text-neutral-400" />
        <div className={`flex items-center gap-2 ${passo >= 3 ? "text-brand-700 font-bold" : "text-neutral-400"}`}>
          <span className="w-5 h-5 rounded-full bg-brand-100 flex items-center justify-center text-[10px]">3</span>
          Mensagem & Disparo
        </div>
      </div>

      {sucesso ? (
        <div className="bg-emerald-50 border border-emerald-200 p-8 rounded-2xl text-center space-y-4">
          <CheckCircle2 className="h-12 w-12 text-emerald-600 mx-auto" />
          <h2 className="text-xl font-bold text-emerald-900">Campanha Salva como Rascunho!</h2>
          <p className="text-xs text-emerald-700">
            Sua campanha &quot;<strong>{nomeCampanha}</strong>&quot; foi salva com {totalElegiveis} contatos elegíveis pré-aprovados.
          </p>
        </div>
      ) : (
        <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-2xs space-y-6">
          {/* PASSO 1: Segmentação */}
          {passo === 1 && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <h2 className="text-sm font-bold text-neutral-900 flex items-center gap-2 border-b pb-2">
                <Users className="h-4 w-4 text-brand-600" /> Passo 1: Nome & Filtros do Segmento
              </h2>

              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-neutral-700">Nome da Campanha:</label>
                  <input
                    type="text"
                    value={nomeCampanha}
                    onChange={(e) => setNomeCampanha(e.target.value)}
                    className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300 focus:outline-hidden focus:border-brand-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-neutral-700">Tipo de Evento:</label>
                    <select
                      value={tipoEvento}
                      onChange={(e) => setTipoEvento(e.target.value)}
                      className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300 bg-white"
                    >
                      <option value="todos">Todos os Eventos</option>
                      <option value="noiva">Noiva / Casamento</option>
                      <option value="debutante">Debutante / 15 Anos</option>
                      <option value="madrinha">Madrinha</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-neutral-700">Status do Úlitmo Lead:</label>
                    <select
                      value={statusLead}
                      onChange={(e) => setStatusLead(e.target.value)}
                      className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300 bg-white"
                    >
                      <option value="todos">Todos os Status</option>
                      <option value="descartado">Descartados (Remarketing)</option>
                      <option value="ganho">Ganhos (Fidelização)</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-3">
                <button
                  onClick={handleCarregarPrevia}
                  disabled={carregandoPrevia}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-brand-600 text-white text-xs font-semibold hover:bg-brand-700 transition"
                >
                  <Eye className="h-4 w-4" />
                  {carregandoPrevia ? "Calculando Prévia..." : "Gerar Prévia da Audiência"}
                </button>
              </div>
            </div>
          )}

          {/* PASSO 2: Prévia e Amostra (AC 2, AC 3) */}
          {passo === 2 && (
            <div className="space-y-5 animate-in fade-in duration-150">
              <h2 className="text-sm font-bold text-neutral-900 flex items-center gap-2 border-b pb-2">
                <Eye className="h-4 w-4 text-brand-600" /> Passo 2: Prévia de Audiência e Amostra
              </h2>

              {/* Box de Contagem e Exclusão LGPD */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-brand-50/60 p-4 rounded-xl border border-brand-200">
                  <div className="text-xs font-semibold text-brand-800">Contatos Elegíveis (Alvos)</div>
                  <div className="text-3xl font-extrabold text-brand-900 mt-1">{totalElegiveis}</div>
                  <p className="text-[11px] text-brand-700 mt-1">Prontos para receber o disparo</p>
                </div>

                <div className="bg-amber-50/60 p-4 rounded-xl border border-amber-200">
                  <div className="text-xs font-semibold text-amber-900 flex items-center gap-1.5">
                    <ShieldCheck className="h-4 w-4 text-amber-600" /> Excluídos por Opt-Out (LGPD)
                  </div>
                  <div className="text-3xl font-extrabold text-amber-950 mt-1">{optoutExcluidos}</div>
                  <p className="text-[11px] text-amber-800 mt-1">Removidos automaticamente da lista (AC 3)</p>
                </div>
              </div>

              {/* Tabela de Amostra Representativa (AC 2) */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-neutral-800">Amostra Representativa (Primeiros 3 contatos):</label>
                <div className="border border-neutral-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-neutral-50 border-b text-neutral-600 font-semibold">
                      <tr>
                        <th className="py-2.5 px-3">Nome</th>
                        <th className="py-2.5 px-3">Telefone</th>
                        <th className="py-2.5 px-3">Tags</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-100">
                      {amostra.map((item) => (
                        <tr key={item.id}>
                          <td className="py-2 px-3 font-semibold text-neutral-900">{item.nome}</td>
                          <td className="py-2 px-3 font-mono text-neutral-600">{item.telefone}</td>
                          <td className="py-2 px-3">
                            <span className="bg-neutral-100 text-neutral-700 px-2 py-0.5 rounded-md text-[10px]">
                              {item.tags.join(", ")}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex justify-between pt-3 border-t">
                <button onClick={() => setPasso(1)} className="px-4 py-2 rounded-lg border border-neutral-300 text-xs font-semibold text-neutral-700 hover:bg-neutral-50">
                  Voltar
                </button>
                <button onClick={() => setPasso(3)} className="px-5 py-2.5 rounded-lg bg-brand-600 text-white text-xs font-semibold hover:bg-brand-700">
                  Avançar para Escolha de Mensagem
                </button>
              </div>
            </div>
          )}

          {/* PASSO 3: Mensagem & Salvamento */}
          {passo === 3 && (
            <div className="space-y-5 animate-in fade-in duration-150">
              <h2 className="text-sm font-bold text-neutral-900 flex items-center gap-2 border-b pb-2">
                <FileText className="h-4 w-4 text-brand-600" /> Passo 3: Mensagem & Finalização
              </h2>

              <div className="space-y-3">
                <label className="text-xs font-semibold text-neutral-700">Selecione o Modelo de Mensagem:</label>
                <select className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-300 bg-white">
                  <option value="msg_1">Lembrete Prova Vestido (Template Meta Aprovado)</option>
                  <option value="msg_2">Segunda Chamada Simples (Texto Livre)</option>
                </select>
              </div>

              <div className="flex justify-between pt-3 border-t">
                <button onClick={() => setPasso(2)} className="px-4 py-2 rounded-lg border border-neutral-300 text-xs font-semibold text-neutral-700 hover:bg-neutral-50">
                  Voltar
                </button>
                <button
                  onClick={handleSalvarRascunho}
                  disabled={salvando}
                  className="px-6 py-2.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 transition"
                >
                  {salvando ? "Salvando..." : "Salvar Rascunho da Campanha"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
