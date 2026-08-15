export type NavCheck = { recurso: string; acao: string };

export type NavItem = {
  label: string;
  href: string;
  // Item visível se o usuário tiver QUALQUER UMA destas permissões
  // (normalmente uma só; "Configurações" agrega 3 porque não há uma
  // permissão-guarda-chuva única para o módulo inteiro em §4.2).
  anyOf: NavCheck[];
};

export const NAV_ITEMS: NavItem[] = [
  { label: "Kanban", href: "/kanban", anyOf: [{ recurso: "lead", acao: "read" }] },
  { label: "Conversas", href: "/conversas", anyOf: [{ recurso: "atendimento", acao: "read" }] },
  { label: "Agenda", href: "/agenda", anyOf: [{ recurso: "agenda", acao: "read" }] },
  { label: "Contatos", href: "/contatos", anyOf: [{ recurso: "contato", acao: "read" }] },
  {
    label: "Configurações",
    href: "/configuracoes",
    anyOf: [
      { recurso: "automacao", acao: "update" },
      { recurso: "canal", acao: "update" },
      { recurso: "ia_config", acao: "update" },
    ],
  },
];
