/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // Let the separate lint step handle errors; don't fail the build
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
