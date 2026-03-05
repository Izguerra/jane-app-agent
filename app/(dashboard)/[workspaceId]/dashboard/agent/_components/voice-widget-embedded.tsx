
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { MessageCircle, Phone, Video } from "lucide-react";
import { ChatSession } from "@/components/chat-session";
import { VoiceSession, AvatarSession } from "@/components/voice-widget";

export function VoiceWidgetEmbedded({ agentId }: { agentId?: string }) {
    const [mode, setMode] = useState<'chat' | 'voice' | 'avatar'>('chat');

    if (!agentId) {
        return (
            <div className="flex flex-col items-center justify-center h-full p-6 text-center text-muted-foreground space-y-4">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center">
                    <span className="text-2xl">🤖</span>
                </div>
                <p>Save your agent to start testing.</p>
                <p className="text-xs">Click "Save Draft" or "Next Step" to generate an ID.</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full">
            <div className="flex justify-center p-2 bg-gray-50 border-b gap-2">
                <Button
                    variant={mode === 'chat' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setMode('chat')}
                    className="h-7 text-xs"
                >
                    <MessageCircle className="h-3 w-3 mr-1" />
                    Chat
                </Button>
                <Button
                    variant={mode === 'voice' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setMode('voice')}
                    className="h-7 text-xs"
                >
                    <Phone className="h-3 w-3 mr-1" />
                    Voice
                </Button>
                <Button
                    variant={mode === 'avatar' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setMode('avatar')}
                    className="h-7 text-xs"
                >
                    <Video className="h-3 w-3 mr-1" />
                    Video
                </Button>
            </div>

            <div className="flex-1 relative overflow-hidden min-h-0">
                {mode === 'chat' ? (
                    <ChatSession embedded={true} agentId={agentId} />
                ) : mode === 'voice' ? (
                    <VoiceSession onClose={() => setMode('chat')} />
                ) : (
                    <AvatarSession onClose={() => setMode('chat')} />
                )}
            </div>
        </div>
    );
}
