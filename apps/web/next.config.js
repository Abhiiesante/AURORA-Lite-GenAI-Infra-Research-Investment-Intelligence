const isStatic = process.env.STATIC_EXPORT === '1';

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // Let the separate lint step handle errors; don't fail the build
    ignoreDuringBuilds: true,
  },
  ...(isStatic ? { output: 'export', images: { unoptimized: true } } : {}),
};

module.exports = nextConfig;
