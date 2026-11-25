import type { NextConfig } from "next";

import { STATIC_SECURITY_HEADERS } from "./lib/security-headers";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },

  // Security headers on every response. The Content-Security-Policy is
  // not here: it carries a per-request nonce, so proxy.ts sets it.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [...STATIC_SECURITY_HEADERS],
      },
      {
        // API routes return patient data; never cache it anywhere.
        source: "/api/:path*",
        headers: [{ key: "Cache-Control", value: "no-store" }],
      },
    ];
  },
};

export default nextConfig;
