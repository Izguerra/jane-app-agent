"use client";

import { ChatSession } from "@/components/chat-session";
import { useParams } from "next/navigation";

export default function ChatEmbedPage() {
    const params = useParams();
    const workspaceId = params.workspaceId ? parseInt(params.workspaceId as string) : undefined;

    if (!workspaceId) {
        return <div className="p-4 text-center">Invalid Workspace ID</div>;
    }

    return (
        <div className="h-screen w-screen bg-transparent">
            <ChatSession workspaceId={workspaceId} className="h-full w-full" />
        </div>
    );
}

