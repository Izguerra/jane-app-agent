import { NextRequest, NextResponse } from 'next/server';
import { getUser, getWorkspaceForUser } from '@/lib/db/queries';

export async function POST(request: NextRequest) {
    try {
        // Authenticate user
        const user = await getUser();
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        // Get team_id from user
        const workspace = await getWorkspaceForUser();
        const teamId = workspace?.teamId;

        if (!teamId) {
            return NextResponse.json({ error: 'No team found' }, { status: 404 });
        }

        // Get request body
        const body = await request.json();
        const {
            to_phone,
            from_phone,
            call_intent,
            customer_id,
            appointment_id,
            deal_id,
            campaign_id,
            campaign_name,
            agent_id
        } = body;

        // Validate required fields
        if (!to_phone) {
            return NextResponse.json({ error: 'to_phone is required' }, { status: 400 });
        }

        // Forward request to FastAPI backend
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${backendUrl}/api/outbound/call`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': user.id.toString(),
                'X-Team-ID': teamId.toString(),
            },
            body: JSON.stringify({
                to_phone,
                from_phone,
                call_intent: call_intent || 'general',
                customer_id,
                appointment_id,
                deal_id,
                campaign_id,
                campaign_name,
                agent_id
            }),
        });

        if (!response.ok) {
            const error = await response.text();
            console.error('Backend error:', error);
            return NextResponse.json(
                { error: error || 'Failed to initiate call' },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('Error initiating outbound call:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}
