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

        const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';

        const response = await fetch(`${backendUrl}/billing/purchase-phone-number`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            // The backend endpoint reads headers/db, body not strictly used but passed if needed
            body: JSON.stringify({})
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            return NextResponse.json(errorData, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error purchasing number:', error);
        return NextResponse.json(
            { detail: 'Internal server error' },
            { status: 500 }
        );
    }
}
