import React from 'react';
import { Check } from 'lucide-react';
import { ToastMessage } from '../../types';

interface ToastProps {
  toast: ToastMessage | null;
  onClose?: () => void;
}

export const Toast: React.FC<ToastProps> = ({ toast }) => {
  if (!toast) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[200] bg-[#072F53] text-[#FAF7F2] px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 animate-fade-in max-w-sm border border-[#1868A8]/30">
      <div className="w-7 h-7 rounded-full bg-[#EBB832] text-[#072F53] grid place-items-center flex-shrink-0 font-bold">
        <Check className="w-4 h-4 stroke-[3]" />
      </div>
      <div>
        <b className="block text-[13px] font-semibold text-white">{toast.title}</b>
        {toast.subtitle && <small className="text-[11px] text-slate-300 opacity-90">{toast.subtitle}</small>}
      </div>
    </div>
  );
};
