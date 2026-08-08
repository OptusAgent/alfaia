import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'sage' | 'wine' | 'gold' | 'slate' | 'amber' | 'mut' | 'navy';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'mut', className = '' }) => {
  const styles = {
    sage: 'bg-[#E5EFE7] text-[#4B7A5B]',
    wine: 'bg-[#F7E8EA] text-[#7B2233]',
    gold: 'bg-[#F2E7D0] text-[#A67C2E]',
    slate: 'bg-[#E5EDF3] text-[#4A6B84]',
    amber: 'bg-[#FBF0DA] text-[#B07A18]',
    mut: 'bg-[#EFE9DE] text-[#8A8076]',
    navy: 'bg-[#E2EDF8] text-[#0E4A7B]',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full font-mono text-[9px] tracking-wider uppercase font-medium whitespace-nowrap ${styles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
