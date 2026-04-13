/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',  // required for Railway/Docker containerized deploys
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
}

module.exports = nextConfig
