import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */

  // Empty turbopack config to silence Next.js 16 warning
  // (Most apps work fine with Turbopack without custom config)
  turbopack: {},

  // Webpack config for react-pdf compatibility (used when --webpack flag is passed)
  webpack: (config) => {
    // Disable canvas for react-pdf compatibility
    config.resolve.alias.canvas = false;
    return config;
  },
};

export default nextConfig;
