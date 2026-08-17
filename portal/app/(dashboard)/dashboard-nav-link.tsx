"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

export function DashboardNavLink({
  href,
  icon,
  label,
}: {
  href: string;
  icon: ReactNode;
  label: string;
}) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link href={href} className="atelier-nav-item" data-active={isActive}>
      <span className="atelier-nav-icon">{icon}</span>
      <span className="truncate">{label}</span>
    </Link>
  );
}
