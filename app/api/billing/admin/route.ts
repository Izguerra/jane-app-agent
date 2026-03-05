import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const timeRange = searchParams.get('time_range') || '30';
    const status = searchParams.get('status') || 'all';
    const type = searchParams.get('type'); // 'stats' or 'invoices'

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

    try {
        let url = '';
        if (type === 'stats') {
            url = `${backendUrl}/billing/admin/stats?time_range=${timeRange}`;
        } else {
            url = `${backendUrl}/billing/admin/invoices?status=${status}&limit=50`;
        }

        const response = await fetch(url, {
            headers: {
                'Cookie': request.headers.get('cookie') || '',
            },
        });

        if (!response.ok) {
            throw new Error('Failed to fetch billing data');
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Billing API error:', error);
        return NextResponse.json(
            { error: 'Failed to fetch billing data' },
            { status: 500 }
        );
    }
}

export async function POST(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const invoiceId = searchParams.get('invoice_id');
    const action = searchParams.get('action'); // 'retry'

    if (action === 'retry' && invoiceId) {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

        try {
            const response = await fetch(
                `${backendUrl}/billing/admin/invoices/${invoiceId}/retry`,
                {
                    method: 'POST',
                    headers: {
                        'Cookie': request.headers.get('cookie') || '',
                    },
                }
            );

            if (!response.ok) {
                throw new Error('Failed to retry payment');
            }

            const data = await response.json();
            return NextResponse.json(data);
        } catch (error) {
            console.error('Payment retry error:', error);
            return NextResponse.json(
                { error: 'Failed to retry payment' },
                { status: 500 }
            );
        }
    }

    return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
}
