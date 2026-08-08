import React from 'react';
import { ProductItem } from '../../types';

interface ProductCardProps {
  product: ProductItem;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  const [color1, color2] = product.g;
  const gradientId = `grad-${color1.replace('#', '')}`;

  return (
    <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-xl p-2 shadow-2xs hover:border-[#0E4A7B] transition-colors">
      <div className="w-9 h-12 rounded-lg overflow-hidden flex-shrink-0 bg-[#FAF7F2] border border-slate-100">
        <svg viewBox="0 0 100 140" className="w-full h-full object-cover">
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={color1} />
              <stop offset="100%" stopColor={color2} />
            </linearGradient>
          </defs>
          <rect width="100" height="140" fill="#F5F1E9" />
          {product.k === 'd' ? (
            /* Dress SVG Path */
            <path
              d="M50 14c-9 0-13 5-13 10l-8 16s-14 44-14 96h70c0-52-14-96-14-96l-8-16c0-5-4-10-13-10z"
              fill={`url(#${gradientId})`}
            />
          ) : (
            /* Suit SVG Path */
            <g>
              <path
                d="M50 16 L32 26 L18 34 L10 130 L90 130 L82 34 L68 26 Z"
                fill={`url(#${gradientId})`}
              />
              <path d="M50 16 L41 62 L50 78 L59 62 Z" fill="rgba(255,255,255,0.9)" />
            </g>
          )}
        </svg>
      </div>

      <div className="min-w-0 flex-1">
        <b className="block text-xs font-semibold text-slate-900 truncate">{product.n}</b>
        <small className="text-[10px] text-slate-500 block truncate">{product.d}</small>
        <div className="font-mono text-xs font-bold text-[#4B7A5B] mt-0.5">{product.p}</div>
      </div>
    </div>
  );
};
