"use client";

import { useActionState } from "react";
import { signIn } from "./actions";
import { ArrowRight, Lock, Mail } from "lucide-react";
import { motion } from "framer-motion";

const initialState: { error: string | null } = { error: null };

export default function LoginPage() {
  const [state, formAction, pending] = useActionState(signIn, initialState);

  return (
    <main
      className="relative flex min-h-screen items-center justify-center px-4 py-12 overflow-hidden"
      style={{ backgroundColor: "var(--bg-primary)" }}
    >
      {/* Atmospheric Glow — Coral blob top-left */}
      <div
        className="pointer-events-none absolute"
        style={{
          top: "15%",
          left: "35%",
          width: "420px",
          height: "420px",
          background: "radial-gradient(circle, rgba(232, 76, 94, 0.18) 0%, transparent 70%)",
          filter: "blur(80px)",
          transform: "translate(-50%, -50%)",
        }}
      />
      {/* Secondary glow — Teal bottom-right (very subtle) */}
      <div
        className="pointer-events-none absolute"
        style={{
          bottom: "10%",
          right: "20%",
          width: "300px",
          height: "300px",
          background: "radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, transparent 70%)",
          filter: "blur(60px)",
        }}
      />

      {/* Login Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 w-full max-w-md"
      >
        <div
          className="glass-card-elevated p-8 sm:p-10"
        >
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.5 }}
            className="mb-8 text-center"
          >
            {/* Logo icon */}
            <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-2xl"
              style={{
                background: "linear-gradient(135deg, var(--accent-primary) 0%, #059669 100%)",
                boxShadow: "var(--shadow-glow-teal)",
              }}
            >
              <svg className="h-6 w-6 fill-current text-black" viewBox="0 0 24 24">
                <path d="M12 2L2 19h20L12 2zm0 4l6.5 11h-13L12 6z" />
              </svg>
            </div>

            <h1
              className="font-display text-3xl font-bold tracking-tight"
              style={{ color: "var(--text-primary)" }}
            >
              Bem-vindo de volta
            </h1>
            <p
              className="mt-2 text-sm"
              style={{ color: "var(--text-secondary)" }}
            >
              Acesse o painel de atendimento ALFAIA
            </p>
          </motion.div>

          {/* Form */}
          <form action={formAction} noValidate className="flex flex-col gap-5">
            {/* Email */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25, duration: 0.5 }}
              className="flex flex-col gap-1.5"
            >
              <label
                htmlFor="email"
                className="text-xs font-semibold uppercase tracking-wider"
                style={{ color: "var(--text-muted)" }}
              >
                E-mail
              </label>
              <div className="relative">
                <Mail
                  className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
                  style={{ color: "var(--text-muted)" }}
                />
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  placeholder="seu.email@empresa.com.br"
                  className="glass-input pl-10"
                />
              </div>
            </motion.div>

            {/* Password */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35, duration: 0.5 }}
              className="flex flex-col gap-1.5"
            >
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="text-xs font-semibold uppercase tracking-wider"
                  style={{ color: "var(--text-muted)" }}
                >
                  Senha
                </label>
                <button
                  type="button"
                  className="text-xs font-medium hover:underline"
                  style={{ color: "var(--accent-primary)" }}
                >
                  Esqueceu a senha?
                </button>
              </div>
              <div className="relative">
                <Lock
                  className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
                  style={{ color: "var(--text-muted)" }}
                />
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  placeholder="••••••••"
                  className="glass-input pl-10 pr-14"
                />
                {/* Submit button inside password field (like reference image) */}
                <button
                  type="submit"
                  disabled={pending}
                  className="absolute right-2 top-1/2 -translate-y-1/2 flex h-8 w-8 items-center justify-center rounded-full transition-all cursor-pointer disabled:opacity-50"
                  style={{
                    background: "linear-gradient(135deg, var(--accent-coral) 0%, #d43f51 100%)",
                    boxShadow: "0 0 12px rgba(232, 76, 94, 0.3)",
                  }}
                >
                  <ArrowRight className="h-4 w-4 text-white" />
                </button>
              </div>
            </motion.div>

            {/* Error State */}
            {state.error && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-lg p-3 text-xs font-medium"
                style={{
                  background: "var(--accent-coral-muted)",
                  color: "var(--accent-coral)",
                  border: "1px solid rgba(232, 76, 94, 0.2)",
                }}
              >
                {state.error}
              </motion.div>
            )}

            {/* Main Submit Button */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.45, duration: 0.5 }}
            >
              <button
                type="submit"
                disabled={pending}
                className="glass-btn glass-btn-primary w-full py-3 text-sm mt-1"
              >
                {pending ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 rounded-full border-2 border-black/30 border-t-black animate-spin" />
                    Autenticando…
                  </span>
                ) : (
                  "Entrar no Portal"
                )}
              </button>
            </motion.div>
          </form>

          {/* Footer divider */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.55, duration: 0.5 }}
            className="mt-6 flex items-center gap-3"
          >
            <div className="h-px flex-1" style={{ background: "var(--bg-glass-border)" }} />
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              ALFAIA
            </span>
            <div className="h-px flex-1" style={{ background: "var(--bg-glass-border)" }} />
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.5 }}
            className="mt-4 text-center text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            CRM Conversacional & Atendimento
          </motion.p>
        </div>
      </motion.div>
    </main>
  );
}
