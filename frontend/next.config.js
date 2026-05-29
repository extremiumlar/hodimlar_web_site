/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Django URL'lari oxirida / ishlatadi (APPEND_SLASH) -
  // Next.js / ni o'chirib 308 redirect qilmasligi uchun:
  skipTrailingSlashRedirect: true,
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "localhost" },
      { protocol: "http", hostname: "127.0.0.1" },
    ],
  },
};

module.exports = nextConfig;
