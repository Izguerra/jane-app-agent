import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
    try {
        // Admin endpoint - fetch global stats
        const response = await fetch(`${BACKEND_URL}/workers/stats?admin=true`);

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}`);
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error fetching admin worker stats:', error);
        return NextResponse.json({
            total_tasks: 0,
            running_tasks: 0,
            completed_tasks: 0,
            failed_tasks: 0,
            avg_rating: null,
            total_revenue_cents: 0
        });
    }
}
