import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
    reactStrictMode: false,
    async rewrites() {
        const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
        return [
            {
                // Proxy all API requests except for migrated native routes
                source: '/api/:path((?!agents|skills|public|diagnostic).*)',
                destination: `${BACKEND_URL}/:path*`,
            },
            {
                source: '/webhooks/:path*',
                destination: `${BACKEND_URL}/webhooks/:path*`, // Proxy Webhooks
            },
            {
                source: '/docs',
                destination: `${BACKEND_URL}/docs`,
            },
            {
                source: '/openapi.json',
                destination: `${BACKEND_URL}/openapi.json`,
            },
        ];
    },
    turbopack: {
        root: '.',
    },
};

export default nextConfig;
