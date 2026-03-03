import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
    reactStrictMode: false,
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://127.0.0.1:8000/:path*', // Proxy API requests
            },
            {
                source: '/webhooks/:path*',
                destination: 'http://127.0.0.1:8000/webhooks/:path*', // Proxy Webhooks
            },
            {
                source: '/docs',
                destination: 'http://127.0.0.1:8000/docs',
            },
            {
                source: '/openapi.json',
                destination: 'http://127.0.0.1:8000/openapi.json',
            },
        ];
    },
    turbopack: {
        root: '.',
    },
};

export default nextConfig;
