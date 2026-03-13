import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(req: NextRequest) {
    try {
        const { searchParams } = new URL(req.url);
        const workspace_id = searchParams.get("workspace_id");

        if (!workspace_id) {
            return NextResponse.json({ error: "workspace_id required" }, { status: 400 });
        }

        const res = await fetch(
            `${BACKEND_URL}/workers/stats?workspace_id=${workspace_id}`,
            {
                headers: { 
                    "Content-Type": "application/json",
                    "Cookie": req.headers.get("cookie") || ""
                },
                cache: "no-store",
                // @ts-ignore
                credentials: "include"
            }
        );

        if (!res.ok) {
            return NextResponse.json({ error: "Failed to fetch stats" }, { status: res.status });
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Workers stats error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
