import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: process.cwd(),
  },
  // Keep the local development overlay from adding a Next.js badge to the site.
  devIndicators: false,
};

export default nextConfig;
