import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    ppr: true,
    clientSegmentCache: true,
    nodeMiddleware: true
  },
  async redirects() {
    return [
      {
        source: '/dashboard/clinic',
        destination: '/dashboard/business',
        permanent: true,
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: '/api/agent/:path*',
        destination: 'http://127.0.0.1:8000/:path*',
      },
      {
        source: '/api/clinics/:path*',
        destination: 'http://127.0.0.1:8000/clinics/:path*',
      },
      {
        source: '/api/phone/:path*',
        destination: 'http://127.0.0.1:8000/phone/:path*',
      },
      {
        source: '/api/integrations/:path*',
        destination: 'http://127.0.0.1:8000/integrations/:path*',
      },
      {
        source: '/api/chat/:path*',
        destination: 'http://127.0.0.1:8000/chat/:path*',
      },
      {
        source: '/api/analytics/:path*',
        destination: 'http://127.0.0.1:8000/analytics/:path*',
      },
      {
        source: '/api/voice/:path*',
        destination: 'http://127.0.0.1:8000/voice/:path*',
      },
      {
        source: '/api/knowledge/:path*',
        destination: 'http://127.0.0.1:8000/knowledge/:path*',
      },
    ];
  },
};

export default nextConfig;
