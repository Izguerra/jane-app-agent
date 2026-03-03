import { NextRequest, NextResponse } from 'next/server';
import { authenticatedFetch } from '@/lib/auth/api';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ workspaceId: string }> }
) {
    try {
        const { workspaceId } = await params;
        const response = await authenticatedFetch(
            `${BACKEND_URL}/workspaces/${workspaceId}/features`
        );

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error fetching workspace features:', errorText);
            return NextResponse.json(
                { error: 'Failed to fetch workspace features' },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error in workspace features API:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}
