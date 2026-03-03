import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function GET(
    request: Request,
    { params }: { params: Promise<{ endpoint: string }> }
) {
    const { endpoint } = await params;

    try {
        const response = await fetch(
            `${BACKEND_URL}/admin/analytics/${endpoint}`,
            {
                headers: {
                    'Cookie': request.headers.get('cookie') || '',
                },
            }
        );

        if (!response.ok) {
            const error = await response.json();
            return NextResponse.json(error, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Analytics API error:', error);
        return NextResponse.json(
            { error: 'Failed to fetch analytics data' },
            { status: 500 }
        );
    }
}
