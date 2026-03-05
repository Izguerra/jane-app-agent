import { NextResponse } from 'next/server';
import { authenticatedFetch } from '@/lib/auth/api';

const getBackendUrl = () => {
    let url = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
    if (url.includes('localhost')) {
        url = url.replace('localhost', '127.0.0.1');
    }
    return url;
};

const BACKEND_URL = getBackendUrl();

export async function POST(request: Request) {
    try {
        const body = await request.json();

        const response = await authenticatedFetch(`${BACKEND_URL}/agents/enhance-soul`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backend enhance-soul error:', response.status, errorText);
            return NextResponse.json(
                { error: 'Failed to enhance soul', details: errorText },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error: any) {
        console.error('Error in enhance-soul proxy:', error);
        return NextResponse.json(
            { error: 'Internal server error', details: error.message },
            { status: 500 }
        );
    }
}
