import { NextResponse } from "next/server";

// QR Code SVG/PNG Base64 mock para visualização perfeita no modal
const MOCK_QRCODE_BASE64 =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'><rect width='200' height='200' fill='%23FAF7F2'/><path d='M20 20h60v60H20zM30 30v40h40V30zM120 20h60v60h-60zM130 30v40h40V30zM20 120h60v60H20zM30 130v40h40v-40z' fill='%23072F53'/><rect x='40' y='40' width='20' height='20' fill='%23EBB832'/><rect x='150' y='40' width='20' height='20' fill='%23EBB832'/><rect x='40' y='150' width='20' height='20' fill='%23EBB832'/><path d='M90 90h20v20H90zM120 120h30v10h-30zM100 140h40v30h-40z' fill='%23072F53'/></svg>";

const mockStatusMap: Record<string, string> = {};

export async function POST(req: Request) {
  try {
    const { nome, telefone } = await req.json();

    if (!nome) {
      return NextResponse.json({ error: "Nome da instância é obrigatório" }, { status: 400 });
    }

    mockStatusMap[nome] = "conectando";

    return NextResponse.json({
      success: true,
      instancia: nome,
      telefone: telefone || null,
      status: "qrcode",
      qrcode: MOCK_QRCODE_BASE64,
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Erro desconhecido";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const instancia = searchParams.get("instancia");

  if (!instancia) {
    return NextResponse.json({ status: "desconectado" });
  }

  const currentStatus = mockStatusMap[instancia] || "conectando";
  return NextResponse.json({ status: currentStatus });
}
