"use client";

import {
    LiveKitRoom,
    RoomAudioRenderer,
    BarVisualizer,
    useVoiceAssistant,
    VoiceAssistantControlBar,
    AgentState,
    useConnectionState,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Phone, X } from "lucide-react";
import { motion } from "framer-motion";

interface VoiceWidgetProps {
    onClose: () => void;
}

export function VoiceWidget({ onClose }: VoiceWidgetProps) {
    const [token, setToken] = useState("");
    const [url, setUrl] = useState("");
    const [error, setError] = useState("");
    const [isReconnecting, setIsReconnecting] = useState(false);
    const [shouldReconnect, setShouldReconnect] = useState(false);

    // Fetch initial token
    useEffect(() => {
        (async () => {
            try {
                const resp = await fetch("/api/agent/voice/token");

                if (!resp.ok) {
                    const errorData = await resp.json();
                    setError(errorData.detail || "Failed to get voice token");
                    return;
                }

                const data = await resp.json();
                console.log("Voice token response:", data);
                if (data.token && data.url) {
                    try {
                        new URL(data.url); // Validate URL
                        setToken(data.token);
                        setUrl(data.url);
                    } catch (e) {
                        console.error("Invalid LiveKit URL:", data.url);
                        setError("Invalid server configuration");
                    }
                } else {
                    setError("Invalid token response from server");
                }
            } catch (e) {
                console.error(e);
                setError("Failed to connect to voice service");
            }
        })();
    }, [shouldReconnect]); // Re-fetch token when shouldReconnect changes

    // Listen for settings changes via SSE
    useEffect(() => {
        // Use relative path which is proxied by Next.js to the backend
        const eventSource = new EventSource("/api/agent/settings/stream");

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "settings_changed") {
                    console.log("Settings changed, reconnecting...", data.data);
                    setIsReconnecting(true);
                    // Trigger reconnection by resetting token
                    setToken("");
                    setTimeout(() => {
                        setShouldReconnect(prev => !prev); // Toggle to trigger useEffect
                        setIsReconnecting(false);
                    }, 1500); // Delay for clean disconnect
                }
            } catch (e) {
                // Ignore parse errors (keepalives)
            }
        };

        return () => {
            eventSource.close();
        };
    }, []);


    const [shouldConnect, setShouldConnect] = useState(true);

    const handleDisconnect = () => {
        setShouldConnect(false);
    };

    if (error) {
        return (
            <div className="p-6 flex flex-col items-center justify-center gap-4 text-center">
                <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                    <X className="h-8 w-8 text-red-500" />
                </div>
                <div className="space-y-2">
                    <h3 className="font-semibold text-lg">Voice Agent Unavailable</h3>
                    <p className="text-sm text-muted-foreground max-w-md">{error}</p>
                </div>
                <Button onClick={onClose} variant="outline" className="mt-2">
                    Close
                </Button>
            </div>
        );
    }

    if (token === "" || isReconnecting) {
        return (
            <div className="p-4 flex flex-col items-center justify-center gap-2">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <div>{isReconnecting ? "Updating settings..." : "Loading voice connection..."}</div>
            </div>
        );
    }

    return (
        <LiveKitRoom
            token={token}
            serverUrl={url}
            connect={shouldConnect}
            audio={true}
            video={false}
            className="flex flex-col items-center justify-center h-full w-full bg-white dark:bg-zinc-950 rounded-lg p-4"
            onDisconnected={onClose}
        >
            <VoiceSessionContent onDisconnect={handleDisconnect} />
            <RoomAudioRenderer />
        </LiveKitRoom>
    );
}

function VoiceSessionContent({ onDisconnect }: { onDisconnect: () => void }) {
    const { state: agentState } = useVoiceAssistant();
    const roomState = useConnectionState();

    const isReady = roomState === "connected" && agentState !== "disconnected";
    const statusText = roomState === "connecting" ? "Connecting..." :
        agentState === "disconnected" ? "Agent Offline" :
            agentState === "connecting" ? "Agent Connecting..." :
                "Agent Ready";

    return (
        <>
            <div className="flex-1 flex flex-col items-center justify-center w-full">
                <div className="relative w-32 h-32 flex items-center justify-center mb-8">
                    {isReady && <div className="absolute inset-0 bg-blue-500/20 rounded-full animate-ping" />}
                    <div className={`relative z-10 w-24 h-24 rounded-full shadow-modern-md flex items-center justify-center transition-colors duration-300 ${isReady ? 'bg-card text-blue-500' : 'bg-muted text-muted-foreground'}`}>
                        <Phone className="h-10 w-10" />
                    </div>
                </div>

                <div className="text-center mb-4 space-y-1">
                    <h3 className="font-medium text-lg">{isReady ? "Jane AI" : "Initializing..."}</h3>
                    <p className={`text-sm ${isReady ? 'text-green-500' : 'text-muted-foreground'}`}>
                        {statusText}
                    </p>
                </div>

                <SimpleVoiceVisualizer />
            </div>

            <div className="w-full max-w-xs">
                <VoiceAssistantControlBar controls={{ leave: false }} />
                <Button
                    onClick={onDisconnect}
                    variant="destructive"
                    className="w-full mt-4 rounded-full"
                >
                    End Call
                </Button>
            </div>
        </>
    );
}

function SimpleVoiceVisualizer() {
    const { state, audioTrack } = useVoiceAssistant();

    return (
        <div className="h-16 flex items-center justify-center gap-1">
            <BarVisualizer
                state={state}
                barCount={5}
                trackRef={audioTrack}
                className="h-full"
                options={{ minHeight: 10, maxHeight: 40 }}
            />
        </div>
    )
}
