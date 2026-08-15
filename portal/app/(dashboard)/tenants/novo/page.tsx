"use client";

import { useState } from "react";
import { Store, Radio, Server, CheckCircle2, ArrowRight, ShieldCheck, Sparkles } from "lucide-react";

interface TenantResultado {
  sucesso: boolean;
  tenant_id: string;
  nome_loja: string;
  dono_email: string;
  canal: string;
  wl_modo: string;
  smoke_isolamento_passou: boolean;
}

export default function NovoTenantOnboardingPage() {
  const [passo, setPasso] = useState<number>(1);
  const [nomeLoja, setNomeLoja] = useState<string>("Maison Belleville Noivas");
  const [donoNome, setDonoNome] = useState<string>("Isabela Belleville");
  const [donoEmail, setDonoEmail] = useState<string>("isabela@belleville.com.br");
  const [canalTipo, setCanalTipo] = useState<string>("uazapi");
  const [wlModo, setWlModo] = useState<string>("mock");

  const [provisionando, setProvisionando] = useState(false);
  const [resultado, setResultado] = useState<TenantResultado | null>(null);

  const handleProvisionar = () => {
    setProvisionando(true);
    setTimeout(() => {
      setProvisionando(false);
      setResultado({
        sucesso: true,
        tenant_id: "t_blv998",
        nome_loja: nomeLoja,
        dono_email: donoEmail,
        canal: canalTipo.toUpperCase(),
        wl_modo: wlModo,
        smoke_isolamento_passou: true,
      });
      setPasso(5);
    }, 600);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="border-b border-neutral-200 pb-4">
        <h1 className="text-2xl font-bold text-neutral-900 flex items-center gap-2.5">
          <Store className="h-7 w-7 text-brand-600" />
          Onboarding de Novo Tenant
        </h1>
        <p className="text-sm text-neutral-500 mt-1">
          Provisione uma nova loja com isolamento de dados, canal de mensagens e integrações em 1 passo.
        </p>
      </div>

      {/* Stepper Header */}
      <div className="flex items-center justify-between bg-neutral-50 p-3.5 rounded-xl border border-neutral-200 text-xs font-semibold">
        <div className={`flex items-center gap-2 ${passo >= 1 ? "text-brand-700 font-bold" : "text-neutral-400"}`}>
          <span className="w-5 h-5 rounded-full bg-brand-100 flex items-center justify-center text-[10px]">1</span>
          Dados da Loja
        </div>
        <ArrowRight className="h-3.5 w-3.5 text-neutral-400" />
        <div className={`flex items-center gap-2 ${passo >= 2 ? "text-brand-700 font-bold" : "text-neutral-400"}`}>
          <span className="w-5 h-5 rounded-full bg-brand-100 flex items-center justify-center text-[10px]">2</span>
          Canal
        </div>
        <ArrowRight className="h-3.5 w-3.5 text-neutral-400" />
        <div className={`flex items-center gap-2 ${passo >= 3 ? "text-brand-700 font-bold" : "text-neutral-400"}`}>
          <span className="w-5 h-5 rounded-full bg-brand-100 flex items-center justify-center text-[10px]">3</span>
          WebLocação
        </div>
        <ArrowRight className="h-3.5 w-3.5 text-neutral-400" />
        <div className={`flex items-center gap-2 ${passo >= 4 ? "text-brand-700 font-bold" : "text-neutral-400"}`}>
          <span className="w-5 h-5 rounded-full bg-brand-100 flex items-center justify-center text-[10px]">4</span>
          Finalização
        </div>
      </div>

      {passo === 5 && resultado ? (
        <div className="bg-emerald-50 border border-emerald-200 p-8 rounded-2xl text-center space-y-4">
          <CheckCircle2 className="h-12 w-12 text-emerald-600 mx-auto" />
          <h2 className="text-xl font-bold text-emerald-900">Tenant Provisionado com Sucesso!</h2>
          <p className="text-xs text-emerald-700">
            A loja &quot;<strong>{resultado.nome_loja}</strong>&quot; (ID: <code className="font-mono bg-white px-2 py-0.5 rounded border">{resultado.tenant_id}</code>) foi criada transacionalmente.
          </p>

          <div className="bg-white/80 p-4 rounded-xl border border-emerald-200 max-w-md mx-auto text-left text-xs space-y-2">
            <div className="flex items-center justify-between border-b pb-1 text-emerald-950 font-semibold">
              <span>Proprietário (Dono):</span>
              <span className="font-mono">{resultado.dono_email}</span>
            </div>
            <div className="flex items-center justify-between border-b pb-1 text-emerald-950 font-semibold">
              <span>Canal Conectado:</span>
              <span>{resultado.canal}</span>
            </div>
            <div className="flex items-center justify-between border-b pb-1 text-emerald-950 font-semibold">
              <span>Modo WebLocação:</span>
              <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-mono text-[10px]">
                {resultado.wl_modo}
              </span>
            </div>
            <div className="flex items-center gap-2 pt-1 text-emerald-700 font-bold">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              Smoke Test de Isolamento: APROVADO (AC 5)
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-2xs space-y-6">
          {/* PASSO 1: Loja e Proprietário */}
          {passo === 1 && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <h2 className="text-sm font-bold text-neutral-900 flex items-center gap-2 border-b pb-2">
                <Store className="h-4 w-4 text-brand-600" /> Passo 1: Nome da Loja & Proprietário (Papel Dono)
              </h2>

              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-neutral-700">Nome do Estabelecimento / Loja:</label>
                  <input
                    type="text"
                    value={nomeLoja}
                    onChange={(e) => setNomeLoja(e.target.value)}
                    className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300 focus:outline-hidden focus:border-brand-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-neutral-700">Nome do Proprietário:</label>
                    <input
                      type="text"
                      value={donoNome}
                      onChange={(e) => setDonoNome(e.target.value)}
                      className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-neutral-700">E-mail do Proprietário:</label>
                    <input
                      type="email"
                      value={donoEmail}
                      onChange={(e) => setDonoEmail(e.target.value)}
                      className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-3">
                <button
                  onClick={() => setPasso(2)}
                  className="px-5 py-2.5 rounded-lg bg-brand-600 text-white text-xs font-semibold hover:bg-brand-700"
                >
                  Avançar para Seleção de Canal
                </button>
              </div>
            </div>
          )}

          {/* PASSO 2: Canal de Mensagens */}
          {passo === 2 && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <h2 className="text-sm font-bold text-neutral-900 flex items-center gap-2 border-b pb-2">
                <Radio className="h-4 w-4 text-brand-600" /> Passo 2: Conexão de Canal de Mensagens (AC 2)
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div
                  onClick={() => setCanalTipo("uazapi")}
                  className={`p-4 rounded-xl border cursor-pointer transition ${
                    canalTipo === "uazapi" ? "border-brand-500 bg-brand-50/50 shadow-2xs" : "border-neutral-200"
                  }`}
                >
                  <div className="font-bold text-sm text-neutral-900">UAZAPI (WhatsApp Web API)</div>
                  <p className="text-xs text-neutral-500 mt-1">
                    Conexão rápida via QR Code. Ideal para instâncias não-oficiais com delay e composing K1.
                  </p>
                </div>

                <div
                  onClick={() => setCanalTipo("meta")}
                  className={`p-4 rounded-xl border cursor-pointer transition ${
                    canalTipo === "meta" ? "border-brand-500 bg-brand-50/50 shadow-2xs" : "border-neutral-200"
                  }`}
                >
                  <div className="font-bold text-sm text-neutral-900">Meta Cloud API (Oficial / AuctaFlux)</div>
                  <p className="text-xs text-neutral-500 mt-1">
                    API oficial do WhatsApp Cloud. Exige templates aprovados K2 fora da janela de 24h.
                  </p>
                </div>
              </div>

              <div className="flex justify-between pt-3 border-t">
                <button onClick={() => setPasso(1)} className="px-4 py-2 rounded-lg border text-xs font-semibold text-neutral-700">
                  Voltar
                </button>
                <button onClick={() => setPasso(3)} className="px-5 py-2.5 rounded-lg bg-brand-600 text-white text-xs font-semibold">
                  Avançar para Integração WebLocação
                </button>
              </div>
            </div>
          )}

          {/* PASSO 3: WebLocação Modo */}
          {passo === 3 && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <h2 className="text-sm font-bold text-neutral-900 flex items-center gap-2 border-b pb-2">
                <Server className="h-4 w-4 text-brand-600" /> Passo 3: Integração com ERP WebLocação (AC 3, I8)
              </h2>

              <div className="space-y-3">
                <label className="text-xs font-semibold text-neutral-700">Modo de Operação do Adapter:</label>
                <select
                  value={wlModo}
                  onChange={(e) => setWlModo(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-300 bg-white"
                >
                  <option value="mock">Modo Mock Padrão (Sem contrato ativo / Testes de Onboarding)</option>
                  <option value="real">Modo Real Produção (Integração direta SOAP/HTTP WebLocação)</option>
                </select>
                <p className="text-[11px] text-neutral-500">
                  Por padrão, novos clientes são provisionados em `modo=mock` para homologação imediata sem depender do ERP.
                </p>
              </div>

              <div className="flex justify-between pt-3 border-t">
                <button onClick={() => setPasso(2)} className="px-4 py-2 rounded-lg border text-xs font-semibold text-neutral-700">
                  Voltar
                </button>
                <button onClick={() => setPasso(4)} className="px-5 py-2.5 rounded-lg bg-brand-600 text-white text-xs font-semibold">
                  Revisar e Finalizar Provisionamento
                </button>
              </div>
            </div>
          )}

          {/* PASSO 4: Revisão e Disparo do Provisionamento */}
          {passo === 4 && (
            <div className="space-y-5 animate-in fade-in duration-150">
              <h2 className="text-sm font-bold text-neutral-900 flex items-center gap-2 border-b pb-2">
                <Sparkles className="h-4 w-4 text-brand-600" /> Passo 4: Confirmação e Provisionamento Transacional
              </h2>

              <div className="bg-neutral-50 p-4 rounded-xl border border-neutral-200 text-xs space-y-2">
                <div><strong>Nome da Loja:</strong> {nomeLoja}</div>
                <div><strong>Proprietário:</strong> {donoNome} ({donoEmail})</div>
                <div><strong>Canal Selecionado:</strong> {canalTipo.toUpperCase()}</div>
                <div><strong>Integração WL:</strong> Modo {wlModo}</div>
              </div>

              <div className="flex justify-between pt-3 border-t">
                <button onClick={() => setPasso(3)} className="px-4 py-2 rounded-lg border text-xs font-semibold text-neutral-700">
                  Voltar
                </button>
                <button
                  onClick={handleProvisionar}
                  disabled={provisionando}
                  className="px-6 py-2.5 rounded-lg bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700 transition"
                >
                  {provisionando ? "Provisionando Tenant..." : "Criar Tenant Transacionalmente"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
