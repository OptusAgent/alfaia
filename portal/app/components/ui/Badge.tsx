import type { ReactNode } from "react";

type BadgeVariant = "success" | "warning" | "danger" | "info" | "purple" | "neutral";

interface BadgeProps {
  variant?: BadgeVariant;
  children: ReactNode;
  icon?: ReactNode;
  pulse?: boolean;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  success: "badge-success",
  warning: "badge-warning",
  danger: "badge-danger",
  info: "badge-info",
  purple: "badge-purple",
  neutral: "badge-neutral",
};

export function Badge({
  variant = "neutral",
  children,
  icon,
  pulse = false,
  className = "",
}: BadgeProps) {
  return (
    <span className={`badge ${variantClasses[variant]} ${className}`}>
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {pulse && (
        <span
          className="h-1.5 w-1.5 rounded-full animate-pulse"
          style={{
            backgroundColor: "currentColor",
          }}
        />
      )}
      {children}
    </span>
  );
}
