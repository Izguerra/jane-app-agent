import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(
    req: NextRequest,
    { params }: { params: { taskId: string } }
) {
    try {
        const taskId = params.taskId;
        const body = await req.json();

        const res = await fetch(`${BACKEND_URL}/workers/tasks/${taskId}/rate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        if (!res.ok) {
            const errorText = await res.text();
            return NextResponse.json({ error: errorText }, { status: res.status });
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Rate task error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
