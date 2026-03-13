import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(req: NextRequest) {
    try {
        const res = await fetch(`${BACKEND_URL}/workers/templates`, {
            headers: { 
                "Content-Type": "application/json",
                "Cookie": req.headers.get("cookie") || ""
            },
            cache: "no-store",
            // @ts-ignore - Some fetch environments need this for cookies
            credentials: "include"
        });

        if (!res.ok) {
            return NextResponse.json({ error: "Failed to fetch templates" }, { status: res.status });
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Workers templates error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
