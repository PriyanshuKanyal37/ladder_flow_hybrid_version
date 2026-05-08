import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["192.168.31.241"],
  turbopack: {
    // Workspace root is one level up from frontend/ — where package.json and node_modules live
    root: path.join(__dirname, ".."),
  },
};

export default nextConfig;
