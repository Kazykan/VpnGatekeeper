import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  allowedDevOrigins: ["miniapp.kocherbaev.ru"],
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Permissions-Policy",
            value: "browsing-topics=()",
          },
        ],
      },
    ]
  },
}

export default nextConfig
