import { NextRequest, NextResponse } from 'next/server';

export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ customerId: string }> }
) {
    const { customerId } = await params;
    const body = await request.json();

    try {
        const response = await fetch(
            `${process.env.NEXT_PUBLIC_BACKEND_URL}/customers/${customerId}/payment-method`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Cookie: request.headers.get('cookie') || '',
                },
                credentials: 'include',
                body: JSON.stringify(body),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            return NextResponse.json(data, { status: response.status });
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Payment method error:', error);
        return NextResponse.json(
            { error: 'Failed to attach payment method' },
            { status: 500 }
        );
    }
}

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ customerId: string }> }
) {
    const { customerId } = await params;

    try {
        const response = await fetch(
            `${process.env.NEXT_PUBLIC_BACKEND_URL}/customers/${customerId}/payment-methods`,
            {
                method: 'GET',
                headers: {
                    Cookie: request.headers.get('cookie') || '',
                },
                credentials: 'include',
            }
        );

        const data = await response.json();

        if (!response.ok) {
            return NextResponse.json(data, { status: response.status });
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Get payment methods error:', error);
        return NextResponse.json(
            { error: 'Failed to get payment methods' },
            { status: 500 }
        );
    }
}
