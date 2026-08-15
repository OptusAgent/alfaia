"use client";

import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  trend?: { value: string; positive: boolean };
  className?: string;
}

export function StatCard({ label, value, icon, trend, className = "" }: StatCardProps) {
  return (
    <div
      className={`glass-card p-4 flex flex-col gap-2 ${className}`}
    >
      <div className="flex items-center justify-between">
        <span
          className="text-xs font-semibold uppercase tracking-wider"
          style={{ color: "var(--text-muted)" }}
        >
          {label}
        </span>
        {icon && (
          <span style={{ color: "var(--accent-primary)" }}>
            {icon}
          </span>
        )}
      </div>
      <div className="flex items-end gap-2">
        <span
          className="text-xl font-bold font-display"
          style={{ color: "var(--text-primary)" }}
        >
          {value}
        </span>
        {trend && (
          <span
            className="text-xs font-semibold mb-0.5"
            style={{
              color: trend.positive ? "var(--accent-primary)" : "var(--accent-coral)",
            }}
          >
            {trend.positive ? "↑" : "↓"} {trend.value}
          </span>
        )}
      </div>
    </div>
  );
}
