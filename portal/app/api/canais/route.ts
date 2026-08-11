import { NextResponse } from "next/server";

// Simulação de banco de dados para a listagem e alternância de canais
let mockCanais = [
  {
    id: "canal-uazapi-01",
    tenant_id: "piloto-01",
    provider: "UAZAPI",
    nome: "WhatsApp Loja Centro (UAZAPI)",
    ativo: true,
    status: "conectado",
    qualidade: "EXCELENTE",
    uazapi_instancia: "loja_centro",
    criado_em: new Date().toISOString(),
  },
  {
    id: "canal-meta-02",
    tenant_id: "piloto-01",
    provider: "META",
    nome: "WhatsApp Oficial (Meta Cloud API / AuctaFlux)",
    ativo: false,
    status: "desconectado",
    qualidade: null,
    uazapi_instancia: null,
    criado_em: new Date().toISOString(),
  },
];

export async function GET() {
  return NextResponse.json({ canais: mockCanais });
}

export async function POST(req: Request) {
  try {
    const { canalId, ativar } = await req.json();

    if (ativar) {
      // Regra AC 1: Apenas 1 canal ativo por tenant (canais_um_ativo)
      mockCanais = mockCanais.map((c) => ({
        ...c,
        ativo: c.id === canalId,
      }));
    } else {
      mockCanais = mockCanais.map((c) => (c.id === canalId ? { ...c, ativo: false } : c));
    }

    return NextResponse.json({ ok: true, canais: mockCanais });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Erro desconhecido";
    return NextResponse.json({ error: msg }, { status: 400 });
  }
}
