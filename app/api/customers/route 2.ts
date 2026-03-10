import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const page = searchParams.get('page') || '1';
    const limit = searchParams.get('limit') || '10';
    const search = searchParams.get('search') || '';

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const url = `${backendUrl}/customers?page=${page}&limit=${limit}${search ? `&search=${search}` : ''}`;

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

export async function POST(request: NextRequest) {
    const body = await request.json();

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const url = `${backendUrl}/customers`;

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Cookie: request.headers.get('cookie') || '',
        },
        body: JSON.stringify(body),
        credentials: 'include',
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
}
