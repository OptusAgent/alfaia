"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

type Variant = "default" | "elevated" | "inset";

interface GlassCardProps {
  children: ReactNode;
  variant?: Variant;
  className?: string;
  delay?: number;
  hover?: boolean;
}

const variantClasses: Record<Variant, string> = {
  default: "glass-card",
  elevated: "glass-card-elevated",
  inset: "glass-card-inset",
};

export function GlassCard({
  children,
  variant = "default",
  className = "",
  delay = 0,
  hover = true,
}: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        delay,
        ease: [0.22, 1, 0.36, 1],
      }}
      whileHover={hover ? { scale: 1.005, y: -1 } : undefined}
      className={`${variantClasses[variant]} ${className}`}
    >
      {children}
    </motion.div>
  );
}
