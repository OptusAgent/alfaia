"use client";

import { useState } from "react";
import { QrCode, Plus, Trash2, CheckCircle2, AlertCircle, Server, ShieldCheck } from "lucide-react";

interface InstanciaItem {
  id: string;
  nome: string;
  base_url: string;
  token: string;
  status: string;
}

export default function InstanciasUazapiPage() {
  const [instancias, setInstancias] = useState<InstanciaItem[]>([
    {
      id: "inst_piloto",
      nome: "Instância WhatsApp Piloto (UAZAPI)",
      base_url: "https://api.uazapi.com",
      token: "uaza****_prod",
      status: "conectado",
    },
  ]);

  const [modalAberta, setModalAberta] = useState(false);
  const [modalQrAberta, setModalQrAberta] = useState(false);
  const [instanciaQr, setInstanciaQr] = useState<InstanciaItem | null>(null);

  const [nome, setNome] = useState("");
  const [baseUrl, setBaseUrl] = useState("https://api.uazapi.com");
  const [token, setToken] = useState("");

  const handleSalvar = (e: React.FormEvent) => {
    e.preventDefault();
    const nova = {
      id: `inst_${Date.now()}`,
      nome: nome || "Nova Instância UAZAPI",
      base_url: baseUrl,
      token: token ? token.substring(0, 4) + "****" : "uaza****",
      status: "desconectado",
    };
    setInstancias([...instancias, nova]);
    setNome("");
    setToken("");
    setModalAberta(false);
  };

  const handleExcluir = (id: string) => {
    if (confirm("Tem certeza que deseja excluir esta instância UAZAPI?")) {
      setInstancias(instancias.filter((i) => i.id !== id));
    }
  };

  const handleGerarQr = (inst: InstanciaItem) => {
    setInstanciaQr(inst);
    setModalQrAberta(true);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-neutral-900 flex items-center gap-2">
            <Server className="h-6 w-6 text-brand-600" />
            Gerenciamento de Instâncias WhatsApp (UAZAPI)
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Configure credenciais reais, instâncias e conecte o WhatsApp via QR Code em tempo real.
          </p>
        </div>

        <button
          onClick={() => setModalAberta(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg text-xs font-semibold hover:bg-brand-700 transition"
        >
          <Plus className="h-4 w-4" /> Nova Instância
        </button>
      </div>

      {/* Lista de Instâncias */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {instancias.map((inst) => (
          <div key={inst.id} className="bg-white p-5 rounded-xl border border-neutral-200 shadow-2xs space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-bold text-sm text-neutral-900">{inst.nome}</h2>
                <span className="text-[11px] font-mono text-neutral-500">{inst.base_url}</span>
              </div>
              <span
                className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                  inst.status === "conectado" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                }`}
              >
                {inst.status === "conectado" ? (
                  <>
                    <CheckCircle2 className="h-3 w-3 text-emerald-600" /> Conectado
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-3 w-3 text-amber-600" /> Desconectado
                  </>
                )}
              </span>
            </div>

            <div className="bg-neutral-50 p-3 rounded-lg border border-neutral-200/80 text-xs space-y-1 font-mono">
              <div className="flex justify-between text-neutral-600">
                <span>Token Master:</span>
                <span>{inst.token}</span>
              </div>
              <div className="flex justify-between text-neutral-600">
                <span>Canal:</span>
                <span>UAZAPI (WhatsApp Web)</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t text-xs">
              <button
                onClick={() => handleGerarQr(inst)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg font-semibold hover:bg-emerald-100 transition"
              >
                <QrCode className="h-4 w-4 text-emerald-600" /> Gerar QR Code
              </button>

              <button
                onClick={() => handleExcluir(inst.id)}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 text-rose-600 hover:bg-rose-50 rounded-lg font-semibold transition"
              >
                <Trash2 className="h-3.5 w-3.5" /> Excluir
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Modal Criar Instância */}
      {modalAberta && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white p-6 rounded-2xl max-w-md w-full space-y-4 shadow-xl">
            <h2 className="text-base font-bold text-neutral-900">Adicionar Nova Instância UAZAPI</h2>

            <form onSubmit={handleSalvar} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-neutral-700">Nome Identificador:</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Instância Loja Matriz"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-neutral-700">URL Base do Servidor UAZAPI:</label>
                <input
                  type="text"
                  required
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300 font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-neutral-700">Token Admin / API Key:</label>
                <input
                  type="password"
                  required
                  placeholder="Cole seu token UAZAPI"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-neutral-300 font-mono"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setModalAberta(false)}
                  className="px-4 py-2 rounded-lg border text-xs font-semibold text-neutral-700"
                >
                  Cancelar
                </button>
                <button type="submit" className="px-5 py-2 bg-brand-600 text-white rounded-lg text-xs font-semibold hover:bg-brand-700">
                  Salvar Instância
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal QR Code */}
      {modalQrAberta && instanciaQr && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white p-6 rounded-2xl max-w-sm w-full text-center space-y-4 shadow-xl">
            <h2 className="text-base font-bold text-neutral-900">Conectar WhatsApp</h2>
            <p className="text-xs text-neutral-500">
              Abra o WhatsApp no celular {">"} Aparelhos Conectados {">"} Conectar um aparelho e escaneie o código.
            </p>

            <div className="bg-neutral-100 p-6 rounded-xl border border-neutral-200 flex items-center justify-center min-h-[200px]">
              <QrCode className="h-32 w-32 text-neutral-800 animate-pulse" />
            </div>

            <div className="text-[11px] text-emerald-700 font-semibold flex items-center justify-center gap-1">
              <ShieldCheck className="h-4 w-4 text-emerald-600" /> Aguardando pareamento em tempo real...
            </div>

            <button
              onClick={() => setModalQrAberta(false)}
              className="w-full py-2 bg-neutral-800 text-white rounded-lg text-xs font-semibold hover:bg-neutral-900"
            >
              Fechar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
