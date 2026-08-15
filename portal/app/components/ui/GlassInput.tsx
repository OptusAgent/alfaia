"use client";

import type { InputHTMLAttributes } from "react";

interface GlassInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  icon?: React.ReactNode;
  error?: string;
}

export function GlassInput({
  label,
  icon,
  error,
  className = "",
  id,
  ...props
}: GlassInputProps) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="text-xs font-semibold uppercase tracking-wider"
          style={{ color: "var(--text-muted)" }}
        >
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <span
            className="absolute left-3 top-1/2 -translate-y-1/2 flex-shrink-0"
            style={{ color: "var(--text-muted)" }}
          >
            {icon}
          </span>
        )}
        <input
          id={inputId}
          className={`glass-input ${icon ? "pl-10" : ""} ${error ? "!border-[var(--accent-coral)]" : ""} ${className}`}
          {...props}
        />
      </div>
      {error && (
        <span className="text-xs" style={{ color: "var(--accent-coral)" }}>
          {error}
        </span>
      )}
    </div>
  );
}
