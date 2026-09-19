import type { NextConfig } from "next";

// FastAPI backend. The browser only ever calls /api/*, which Next proxies here, so a
// phone on an HTTPS tunnel needs a single URL (camera + mic require HTTPS off localhost).
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Dev server blocks cross-origin dev assets by default; allow the tunnel hosts.
  allowedDevOrigins: ["*.ngrok-free.app", "*.ngrok.app", "*.trycloudflare.com"],
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_URL}/:path*` }];
  },
};

export default nextConfig;
