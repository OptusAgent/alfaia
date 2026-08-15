import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Necessario para o build Docker (Dockerfile) copiar so o runtime minimo,
  // nao a arvore inteira de node_modules — mesma imagem serve Cloud Run e VPS.
  output: "standalone",
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
