import { NextRequest, NextResponse } from 'next/server';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ workspaceId: string }> }
) {
    const { workspaceId } = await params;
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const url = `${backendUrl}/workspaces/${workspaceId}`;

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

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ workspaceId: string }> }
) {
    const { workspaceId } = await params;
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const url = `${backendUrl}/workspaces/${workspaceId}`;
    const body = await request.json();

    const response = await fetch(url, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            Cookie: request.headers.get('cookie') || '',
        },
        credentials: 'include',
        body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
}
