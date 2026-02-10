import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  experimental: {
    // Allow large file uploads (500MB)
    bodySizeLimit: '500mb',
  },
};

export default nextConfig;
