"use client";

import { useActionState } from "react";
import { signIn } from "./actions";

const initialState: { error: string | null } = { error: null };

export default function LoginPage() {
  const [state, formAction, pending] = useActionState(signIn, initialState);

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#FAF7F2] px-4 py-12">
      <div className="w-full max-w-md rounded-2xl border border-[#E7DFD2] bg-white p-8 shadow-[0_8px_24px_-14px_rgba(31,27,23,0.16)]">
        {/* Header Logo */}
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#A67C2E] to-[#6E4F17] text-white shadow-[0_6px_16px_-8px_rgba(166,124,46,0.8)]">
            <svg className="h-5 w-5 fill-current" viewBox="0 0 24 24">
              <path d="M12 2L2 19h20L12 2zm0 4l6.5 11h-13L12 6z" />
            </svg>
          </div>
          <div>
            <h1 className="font-serif text-2xl font-bold tracking-wide text-[#1F1B17] leading-none">
              ALFAIA
            </h1>
            <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-[#B3A99C] block mt-1">
              CRM CONVERSACIONAL & ATENDIMENTO
            </span>
          </div>
        </div>

        <p className="mb-6 text-sm text-[#544C43]">
          Informe suas credenciais para acessar o painel de atendimento.
        </p>

        <form action={formAction} noValidate className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-xs font-semibold uppercase tracking-wider text-[#544C43]">
              E-mail corporativo
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              placeholder="seu.email@empresa.com.br"
              className="w-full rounded-lg border border-[#E7DFD2] bg-white px-3.5 py-2.5 text-sm text-[#1F1B17] placeholder-[#B3A99C] shadow-xs outline-none transition-all focus:border-[#A67C2E] focus:ring-2 focus:ring-[#A67C2E]/20"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-xs font-semibold uppercase tracking-wider text-[#544C43]">
              Senha de acesso
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              placeholder="••••••••"
              className="w-full rounded-lg border border-[#E7DFD2] bg-white px-3.5 py-2.5 text-sm text-[#1F1B17] placeholder-[#B3A99C] shadow-xs outline-none transition-all focus:border-[#A67C2E] focus:ring-2 focus:ring-[#A67C2E]/20"
            />
          </div>

          {state.error && (
            <div className="rounded-lg bg-[#F7E8EA] border border-[#7B2233]/20 p-3 text-xs text-[#7B2233]">
              {state.error}
            </div>
          )}

          <button
            type="submit"
            disabled={pending}
            className="mt-2 w-full rounded-lg bg-[#A67C2E] px-4 py-2.5 text-sm font-semibold text-white shadow-xs transition-all hover:bg-[#8E6723] active:scale-[0.99] disabled:opacity-60 cursor-pointer"
          >
            {pending ? "Autenticando…" : "Entrar no Portal"}
          </button>
        </form>
      </div>
    </main>
  );
}

