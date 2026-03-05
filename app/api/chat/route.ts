import { NextRequest, NextResponse } from 'next/server';
import { getAuthToken } from '@/lib/auth/api';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
    try {
        const token = await getAuthToken();
        if (!token) {
            return NextResponse.json(
                { detail: 'Unauthorized' },
                { status: 401 }
            );
        }

        let backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
        if (backendUrl.includes('localhost')) {
            backendUrl = backendUrl.replace('localhost', '127.0.0.1');
        }

        const body = await request.json();

        const response = await fetch(`${backendUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            return NextResponse.json(
                errorData,
                { status: response.status }
            );
        }

        // Return the raw readable stream directly to the client
        return new NextResponse(response.body, {
            headers: {
                'Content-Type': 'text/plain; charset=utf-8',
                'Transfer-Encoding': 'chunked',
            },
        });
    } catch (error) {
        console.error('Error in chat proxy:', error);
        return NextResponse.json(
            { detail: 'Failed to process chat request' },
            { status: 500 }
        );
    }
}
