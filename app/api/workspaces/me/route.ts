import { NextRequest, NextResponse } from 'next/server';
import { authenticatedFetch } from '@/lib/auth/api';

const BACKEND_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';

export async function GET() {
    try {
        const response = await authenticatedFetch(`${BACKEND_URL}/workspaces/me`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backend error:', response.status, errorText);
            return NextResponse.json(
                { error: 'Failed to fetch workspace data', details: errorText },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error: any) {
        console.error('Error fetching workspace:', error);
        return NextResponse.json(
            { error: 'Internal server error', details: error.message },
            { status: 500 }
        );
    }
}

export async function PUT(request: NextRequest) {
    try {
        const body = await request.json();
        console.log('Updating workspace with data:', body);

        const response = await authenticatedFetch(`${BACKEND_URL}/workspaces/me`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backend error:', response.status, errorText);
            return NextResponse.json(
                { error: 'Failed to update workspace data', details: errorText },
                { status: response.status }
            );
        }

        const data = await response.json();
        console.log('Update successful:', data);
        return NextResponse.json(data);
    } catch (error: any) {
        console.error('Error updating workspace:', error);
        return NextResponse.json(
            { error: 'Failed to update workspace data', details: error.message },
            { status: 500 }
        );
    }
}
