import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: process.env.VERCEL ? undefined : "standalone",
  transpilePackages: ["@supabase/ssr", "@supabase/supabase-js"],
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  async redirects() {
    return [
      {
        source: "/",
        destination: "/kanban",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
