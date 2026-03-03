import { NextRequest, NextResponse } from 'next/server';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ customerId: string }> }
) {
    const { customerId } = await params;
    const { searchParams } = new URL(request.url);
    const periodType = searchParams.get('period_type') || 'month';
    const periodValue = searchParams.get('period_value') || '';

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const url = `${backendUrl}/customers/${customerId}/analytics?period_type=${periodType}&period_value=${periodValue}`;

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
