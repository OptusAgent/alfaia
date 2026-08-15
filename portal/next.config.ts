import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Se estiver na Vercel, deixa o runtime padrao da Vercel.
  // Se for Docker/Cloud Run/VPS local, ativa standalone.
  output: undefined,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
