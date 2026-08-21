import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["mapbox-gl"],
};

export default nextConfig;
