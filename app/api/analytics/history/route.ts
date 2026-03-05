import { NextResponse } from 'next/server';
import { authenticatedFetch } from '@/lib/auth/api';

const getBackendUrl = () => {
    let url = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    if (url.includes('localhost')) {
        url = url.replace('localhost', '127.0.0.1');
    }
    return url;
};

const BACKEND_URL = getBackendUrl();

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const workspaceId = searchParams.get('workspaceId');

        let url = `${BACKEND_URL}/analytics/history`;
        if (workspaceId) url += `?workspaceId=${workspaceId}`;

        const response = await authenticatedFetch(url);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backend error:', response.status, errorText);
            return NextResponse.json(
                { error: 'Failed to fetch analytics history', details: errorText },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error: any) {
        console.error('Error fetching analytics history:', error);
        return NextResponse.json(
            { error: 'Internal server error', details: error.message },
            { status: 500 }
        );
    }
}
