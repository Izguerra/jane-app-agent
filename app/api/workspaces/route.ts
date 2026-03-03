import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const url = `${backendUrl}/workspaces`;

    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            Cookie: request.headers.get('cookie') || '',
        },
        credentials: 'include',
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
}

export async function PATCH(request: NextRequest) {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const body = await request.json();
    const { workspaceId, status } = body;

    const url = `${backendUrl}/workspaces/${workspaceId}/status`;

    const response = await fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            Cookie: request.headers.get('cookie') || '',
        },
        credentials: 'include',
        body: JSON.stringify({ status }),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
}
