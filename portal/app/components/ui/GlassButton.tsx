"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "danger" | "ghost";

interface GlassButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  children: ReactNode;
  icon?: ReactNode;
}

const variantClasses: Record<Variant, string> = {
  primary: "glass-btn glass-btn-primary",
  danger: "glass-btn glass-btn-danger",
  ghost: "glass-btn glass-btn-ghost",
};

export function GlassButton({
  variant = "primary",
  children,
  icon,
  className = "",
  ...props
}: GlassButtonProps) {
  return (
    <button
      className={`${variantClasses[variant]} ${className}`}
      {...props}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </button>
  );
}
