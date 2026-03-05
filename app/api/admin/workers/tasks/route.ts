import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
    try {
        // Admin endpoint - fetch all tasks across all workspaces
        const response = await fetch(`${BACKEND_URL}/workers/tasks?admin=true&limit=100`);

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}`);
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error fetching admin worker tasks:', error);
        return NextResponse.json(
            { error: 'Failed to fetch tasks', tasks: [] },
            { status: 500 }
        );
    }
}
