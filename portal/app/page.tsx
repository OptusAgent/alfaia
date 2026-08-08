import { redirect } from "next/navigation";

// Raiz só decide para onde ir — middleware já garante que não autenticado
// nunca chega aqui (redireciona para /login antes).
export default function RootPage() {
  redirect("/kanban");
}
