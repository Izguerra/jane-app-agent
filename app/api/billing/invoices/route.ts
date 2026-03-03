import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET() {
    const cookieStore = await cookies();
    const session = cookieStore.get('session');

    if (!session) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const res = await fetch(`${BACKEND_URL}/billing/invoices`, {
            method: 'GET',
            headers: {
                'Cookie': `session=${session.value}`,
                'Content-Type': 'application/json'
            }
        });

        if (!res.ok) {
            return NextResponse.json({ error: 'Failed to fetch invoices' }, { status: res.status });
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Billing Invoices Error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
