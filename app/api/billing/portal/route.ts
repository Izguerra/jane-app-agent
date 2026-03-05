import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: Request) {
    const cookieStore = await cookies();
    const session = cookieStore.get('session');

    if (!session) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        // Get referer from client request to pass to backend?
        const referer = request.headers.get('referer');

        const res = await fetch(`${BACKEND_URL}/billing/portal`, {
            method: 'POST',
            headers: {
                'Cookie': `session=${session.value}`,
                'Content-Type': 'application/json',
                'Referer': referer || ''
            }
        });

        if (!res.ok) {
            const err = await res.text();
            return NextResponse.json({ error: err }, { status: res.status });
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Billing Portal Error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
