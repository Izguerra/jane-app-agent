import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(req: NextRequest) {
    try {
        const { searchParams } = new URL(req.url);
        const workspace_id = searchParams.get("workspace_id");

        if (!workspace_id) {
            return NextResponse.json({ error: "workspace_id required" }, { status: 400 });
        }

        const limit = searchParams.get("limit") || "50";
        const offset = searchParams.get("offset") || "0";
        const status = searchParams.get("status");

        let url = `${BACKEND_URL}/workers/tasks?workspace_id=${workspace_id}&limit=${limit}&offset=${offset}`;
        if (status) {
            url += `&status=${status}`;
        }

        const res = await fetch(
            url,
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
            return NextResponse.json({ error: "Failed to fetch tasks" }, { status: res.status });
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Workers tasks error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}

export async function POST(req: NextRequest) {
    try {
        const { searchParams } = new URL(req.url);
        const workspace_id = searchParams.get("workspace_id");

        if (!workspace_id) {
            return NextResponse.json({ error: "workspace_id required" }, { status: 400 });
        }

        const body = await req.json();

        const res = await fetch(
            `${BACKEND_URL}/workers/tasks?workspace_id=${workspace_id}`,
            {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Cookie": req.headers.get("cookie") || ""
                },
                body: JSON.stringify(body),
                // @ts-ignore
                credentials: "include"
            }
        );

        if (!res.ok) {
            const errorText = await res.text();
            return NextResponse.json({ error: errorText }, { status: res.status });
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Create task error:", error);
        return NextResponse.json({ error: "Internal server error" }, { status: 500 });
    }
}
