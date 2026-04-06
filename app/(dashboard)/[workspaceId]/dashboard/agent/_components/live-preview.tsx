
"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AgentFormData } from "./types";
import { Send, User as UserIcon, Bot as BotIcon, X, Phone, Video, Bot, Camera, CameraOff, RefreshCw, MessageSquare, MessageSquareOff } from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Maximize2, Minimize2, Settings2, Layout, Monitor, Square, Layers, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import {
    LiveKitRoom,
    RoomAudioRenderer,
    BarVisualizer,
    useVoiceAssistant,
    useConnectionState,
    useLocalParticipant,
    useTracks,
    VideoTrack,
    useTranscriptions,
    useParticipants,
    useTrackToggle,
} from "@livekit/components-react";
import { AgentAudioVisualizerAura } from "@/components/agents-ui/agent-audio-visualizer-aura";

import { Track } from "livekit-client";
import "@livekit/components-styles";
import { Mic, MicOff } from "lucide-react";
import { cn } from "@/lib/utils";
import dynamic from 'next/dynamic';
const Markdown = dynamic(() => import('markdown-to-jsx'), { ssr: false });
import { ConnectionDiagnostics } from "./connection-diagnostics";

// Dummy RequestAudioPermission if not existing (LiveKit usually handles this internally or via prop)
const RequestAudioPermission = () => null;

type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'transitioning' | 'error';
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_DELAY_MS = 2000;

interface LivePreviewProps {
    formData: AgentFormData;
    agentId?: string;
    workspaceId?: string;
    voiceToken?: { token: string; url: string } | null;  // Pre-generated token from parent
    setFormData?: React.Dispatch<React.SetStateAction<AgentFormData>>;
    unavailable?: boolean;
}

export function LivePreview({ formData, agentId, workspaceId, voiceToken, setFormData, unavailable }: LivePreviewProps) {
    const [mode, setMode] = useState<'chat' | 'voice' | 'avatar'>('chat');
    const [messages, setMessages] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [input, setInput] = useState("");
    const scrollRef = useRef<HTMLDivElement>(null);

    // LiveKit State
    const [token, setToken] = useState("");
    const [url, setUrl] = useState("");
    const [isConnecting, setIsConnecting] = useState(false);
    const [error, setError] = useState("");
    const [imgError, setImgError] = useState(false);
    const [headerImgError, setHeaderImgError] = useState(false);
    const isReconnecting = useRef(false);
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('idle');
    const intentionalDisconnect = useRef(false);
    const reconnectAttempts = useRef(0);
    const reconnectTimer = useRef<NodeJS.Timeout | null>(null);

    // Cleanup reconnect timer on unmount
    useEffect(() => {
        return () => {
            if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
        };
    }, []);

    // Reconnection handler
    const handleDisconnected = useCallback((reason?: any) => {
        console.log("DEBUG: LivePreview onDisconnected", { intentional: intentionalDisconnect.current, switching: isSwitchingMode.current, attempts: reconnectAttempts.current, reason });

        // If we're switching modes (voice→avatar, avatar→voice, etc.), skip reconnect logic
        if (isSwitchingMode.current) {
            isSwitchingMode.current = false;
            console.log("DEBUG: Mode switch disconnect — skipping reconnect");
            return;
        }

        if (intentionalDisconnect.current) {
            intentionalDisconnect.current = false;
            setConnectionStatus('idle');
            setToken("");
            setUrl("");
            setMode('chat');
            return;
        }

        if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
            console.log("DEBUG: Max reconnect attempts reached");
            setConnectionStatus('error');
            return;
        }

        setConnectionStatus('reconnecting');
        reconnectAttempts.current += 1;

        reconnectTimer.current = setTimeout(() => {
            console.log(`DEBUG: Reconnection attempt ${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS}`);
            setToken(""); // Clear token to trigger re-fetch
            setUrl("");
        }, RECONNECT_DELAY_MS);
    }, []);

    const handleConnected = useCallback(() => {
        console.log("DEBUG: [agentId] LivePreview handleConnected - setting status to connected");
        reconnectAttempts.current = 0;
        setConnectionStatus('connected');
    }, []);

    const handleEndCall = useCallback(async () => {
        intentionalDisconnect.current = true;
        setToken("");
        setUrl("");
        setMode('chat');
        // Clean up server-side rooms
        if (agentId && agentId !== 'new') {
            try {
                await fetch("/api/voice/cleanup-room", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ agent_id: agentId })
                });
            } catch (e) {
                console.warn("Room cleanup on end call failed (non-critical):", e);
            }
        }
    }, [agentId]);

    const handleModeSwitch = async (targetMode: 'chat' | 'voice' | 'avatar') => {
        if (mode === targetMode) return;
        
        // CLEAN BREAK: Always go through chat first with server-side room cleanup
        if (mode === 'voice' || mode === 'avatar') {
            await toast.promise(
                new Promise(async (resolve) => {
                    // 1. Mark as intentional disconnect to prevent reconnect logic
                    isSwitchingMode.current = true;
                    intentionalDisconnect.current = true;
                    setConnectionStatus('transitioning');
                    
                    // 2. Drop to chat mode immediately to unmount LiveKitRoom
                    setToken("");
                    setUrl("");
                    setMode('chat');
                    
                    // 3. Server-side cleanup: explicitly delete old rooms
                    if (agentId && agentId !== 'new') {
                        try {
                            await fetch("/api/voice/cleanup-room", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ agent_id: agentId })
                            });
                        } catch (e) {
                            console.warn("Room cleanup request failed (non-critical):", e);
                        }
                    }
                    
                    // 4. Brief propagation delay for LiveKit to fully tear down
                    await new Promise(r => setTimeout(r, 1000));
                    
                    // 5. Reset connection state
                    reconnectAttempts.current = 0;
                    setConnectionStatus('idle');
                    isSwitchingMode.current = false;
                    intentionalDisconnect.current = false;
                    
                    resolve(true);
                }),
                {
                    loading: `Shutting down ${mode} session...`,
                    success: targetMode === 'chat' ? 'Session ended' : `Starting ${targetMode} mode`,
                    error: 'Transition failed',
                }
            );
            
            // 6. If target is not chat, switch to new mode (triggers token fetch)
            if (targetMode !== 'chat') {
                setMode(targetMode);
            }
            return;
        }
        
        // Simple switch from chat → voice/avatar
        if (targetMode === 'voice' || targetMode === 'avatar') {
            toast.info(`Initializing ${targetMode} agent...`);
        }
        
        setMode(targetMode);
    };


    const handleRetry = useCallback(() => {
        reconnectAttempts.current = 0;
        setConnectionStatus('connecting');
        setToken("");
        setUrl("");
    }, []);

    // UI Enhancements (Phase 5)
    const [isTheaterMode, setIsTheaterMode] = useState(false);
    const [pipSize, setPipSize] = useState<'sm' | 'md' | 'lg'>('sm');
    const [showCaptions, setShowCaptions] = useState(true);

    useEffect(() => {
        setImgError(false);
    }, [formData.avatarUrl, formData.widgetIconUrl]);

    // Auto-scroll to bottom when messages change
    // Auto-scroll to bottom when messages change
    useEffect(() => {
        if (scrollRef.current) {
            const { scrollHeight, clientHeight } = scrollRef.current; // Get the values from the current scrollRef
            // Only scroll if the content is taller than the container
            if (scrollHeight > clientHeight) {
                scrollRef.current.scrollTo({
                    top: scrollHeight - clientHeight,
                    behavior: "smooth"
                });
            }
        }
    }, [messages]);

    // Update messages when welcome greeting changes
    // Update messages when welcome greeting or language changes
    useEffect(() => {
        if (unavailable) return;

        const updateGreeting = async () => {
            let greeting = formData.welcomeGreeting || "Hello! How can I help you?";

            if (formData.language && formData.language !== 'en') {
                try {
                    const res = await fetch('/api/settings/translate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            text: greeting,
                            target_language: formData.language
                        })
                    });
                    if (res.ok) {
                        const data = await res.json();
                        greeting = data.translated_text;
                    }
                } catch (e) {
                    console.error("Translation failed", e);
                }
            }

            setMessages([
                { role: 'assistant', content: greeting }
            ]);
        };

        // Debounce to prevent too many API calls while typing
        const timer = setTimeout(updateGreeting, 1000);
        return () => clearTimeout(timer);

    }, [formData.welcomeGreeting, formData.language, unavailable]);

    // Helper to construct agent config from form data
    const getAgentConfig = () => ({
        name: formData.name,
        voice_id: formData.voice_id || "alloy",
        language: formData.language,
        // Reconstruct prompt logic to match backend/page.tsx logic
        prompt_template: `You are ${formData.name}, a ${formData.conversationStyle} assistant. ${formData.businessDescription}`,
        welcome_message: formData.welcomeGreeting,
        creativity_level: Number(formData.creativityLevel || 50),
        response_length: Number(formData.responseLength || 50),
        intent_rules: JSON.stringify(formData.intentRules || []),
        allowed_worker_types: formData.allowedWorkerTypes || [],

        // Agent Type & Personal Profile
        agent_type: formData.agentType || "business",
        owner_name: formData.ownerName,
        personal_location: formData.location,
        personal_timezone: formData.timezone,
        favorite_foods: formData.favoriteFoods,
        favorite_restaurants: formData.favoriteRestaurants,
        favorite_music: formData.favoriteMusic,
        favorite_activities: formData.favoriteActivities,
        other_interests: formData.otherInterests,
        personal_likes: formData.likes,
        personal_dislikes: formData.dislikes,

        // Avatar Context
        tavus_replica_id: formData.tavusReplicaId,
        tavus_persona_id: formData.tavusPersonaId,
        anam_persona_id: formData.anamPersonaId,
        avatar_provider: formData.avatarProvider || (formData.anamPersonaId ? 'anam' : (formData.tavusReplicaId ? 'tavus' : undefined)),
        avatar_voice_id: formData.avatarVoiceId,
        use_tavus_avatar: formData.useTavusAvatar,

        // KB Context
        business_name: formData.businessName,
        website_url: formData.websiteUrl,
        email: formData.email,
        phone: formData.phone,
        address: formData.address,
        services: formData.services,
        hours_of_operation: formData.hoursOfOperation,
        faq: JSON.stringify(formData.faqItems || []),
        accent_color: formData.accentColor,
        mode: mode,
        open_claw_instance_id: formData.openClawInstanceId,

        // Ephemeral Browser Context
        client_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        // @ts-ignore
        client_location: window.clientLocationData || "Unknown location"
    });

    // Reset image error states when avatar data changes
    useEffect(() => {
        setImgError(false);
        setHeaderImgError(false);
    }, [formData.avatarUrl, formData.useTavusAvatar]);

    // Fetch precise location on mount
    useEffect(() => {
        if (typeof window !== "undefined" && navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    // @ts-ignore
                    window.clientLocationData = `${position.coords.latitude},${position.coords.longitude}`;
                },
                (error) => {
                    // Only log if it's not a denial
                    if (error.code !== error.PERMISSION_DENIED) {
                        console.log("Geolocation error:", error);
                    }
                }
            );
        }
    }, []);

    // Simple mode-switch handler: clear token when mode changes so a fresh connection is made.
    // This follows the proven working pattern from voice-widget.tsx (commits 589e02e, 2298776):
    // mode switch → unmount LiveKitRoom → clear token → delay → token fetch effect gets new token → remount LiveKitRoom
    const prevMode = useRef(mode);
    const isSwitchingMode = useRef(false);
    useEffect(() => {
        if (prevMode.current !== mode) {
            console.log(`DEBUG: Mode switched from ${prevMode.current} to ${mode}. Clearing token for fresh connection.`);
            // Mark as intentional switch so handleDisconnected doesn't trigger reconnect
            if ((prevMode.current === 'voice' || prevMode.current === 'avatar') && 
                (mode === 'voice' || mode === 'avatar' || mode === 'chat')) {
                isSwitchingMode.current = true;
            }
            prevMode.current = mode;
            
            // STABILIZATION FIX: Set transitioning status and add delay before clearing token.
            // This ensures the old LiveKit connection fully disconnects before
            // the new token fetch trigger fires.
            if (mode === 'voice' || mode === 'avatar') {
                setConnectionStatus('transitioning');
            } else {
                setConnectionStatus('idle');
            }
            setToken("");
            setUrl("");
            setError("");
        }
    }, [mode]);


    const tokenFetchInProgress = useRef(false);

    // Fetch Token on Voice Mode
    useEffect(() => {
        if (unavailable) return;

        if ((mode === 'voice' || mode === 'avatar') && !token) {
            // Note: We deliberately DO NOT reuse any pre-generated tokens from the parent.
            // Why? Reusing a token bypasses the backend POST /api/voice/token endpoint. 
            // The backend endpoint is responsible for explicitly dispatching the AI agent.
            // If we reuse a token, the user enters the room but the agent is never dispatched.
            // This guarantees a fresh dispatch on every call initialization.

            // Guard against React StrictMode double-execution race conditions
            if (tokenFetchInProgress.current) return;
            tokenFetchInProgress.current = true;

            // This is for cases where user hasn't saved yet but wants to preview
            if (!agentId || agentId === 'new') {
                setError("Please save the agent first to enable voice/video preview");
                setIsConnecting(false);
                tokenFetchInProgress.current = false;
                return;
            }

            if (mode === 'avatar' && !formData.tavusReplicaId && !formData.anamPersonaId) {
                // Do not connect if no avatar is selected
                setError("Please select an avatar to start.");
                setIsConnecting(false);
                tokenFetchInProgress.current = false;
                return;
            }

            setIsConnecting(true);
            setError("");
            (async () => {
                try {
                    // STABILITY FIX: Clean up any stale rooms from previous sessions
                    // This prevents duplicate agent dispatch (one auto-dispatched + one explicit)
                    // which causes the "3 participants → 2 participants" drop pattern
                    if (agentId && agentId !== 'new') {
                        try {
                            await fetch("/api/voice/cleanup-room", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ agent_id: agentId })
                            });
                            // Brief delay for LiveKit to process the room deletion
                            await new Promise(r => setTimeout(r, 500));
                        } catch (cleanupErr) {
                            console.warn("Pre-connection room cleanup failed (non-critical):", cleanupErr);
                        }
                    }

                    // Only send agent_id and workspace_id - let backend use saved DB data
                    const resp = await fetch("/api/voice/token", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            agent_id: agentId,
                            workspace_id: workspaceId,
                            agent_config: getAgentConfig(), // Use current wizard data
                            mode: mode
                        })
                    });

                    if (!resp.ok) {
                        const err = await resp.json();
                        throw new Error(err.detail || "Failed to get token");
                    }
                    const data = await resp.json();
                    setToken(data.token);
                    setUrl(data.url);
                    isReconnecting.current = false;
                } catch (e) {
                    console.error(e);
                    setError("Failed to connect to voice service");
                } finally {
                    setIsConnecting(false);
                    tokenFetchInProgress.current = false;
                }
            })();
        }

    }, [mode, agentId, token, voiceToken, workspaceId, formData.tavusReplicaId, formData.anamPersonaId, formData.useTavusAvatar, unavailable]);
    // Added explicit dependency on replicaID to trigger new token fetch if avatar changes
    // Removed formData dependency - token should use saved data, not form state 
    // But token is state. If token exists, it won't fetch. So we need to clear token if formData changes?
    // For now, let's keep it simple: It fetches when entering voice mode.

    const handleSend = async () => {
        if (unavailable) return;
        if (!input.trim() || isLoading) return;

        const userMessage = { role: 'user' as const, content: input };
        const newMsgs = [...messages, userMessage];
        setMessages(newMsgs);
        setInput("");
        setIsLoading(true);

        // 1. Check FAQ items locally (optional simple filter)
        const lowerInput = input.toLowerCase();
        let clientResponse = null;

        const faqMatch = formData.faqItems.find(item => {
            if (!item.question?.trim()) return false;
            const qLower = item.question.toLowerCase();
            return lowerInput.includes(qLower) || qLower.includes(lowerInput);
        });

        if (faqMatch) {
            clientResponse = faqMatch.answer;
        }

        if (clientResponse) {
            setMessages(prev => [...prev, { role: 'assistant', content: clientResponse! }]);
            setIsLoading(false);
            return;
        }

        // 2. Call Real API
        try {
            const agentConfig = getAgentConfig();

            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: input,
                    agent_id: agentId,
                    agent_config: agentConfig,
                    history: newMsgs.map(m => ({ role: m.role, content: m.content }))
                })
            });

            if (!response.ok) throw new Error("Failed to get response");

            // Read stream
            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            setMessages(prev => [...prev, { role: 'assistant', content: "" }]);

            if (reader) {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    setMessages(prev => {
                        const newMessages = [...prev];
                        const lastIndex = newMessages.length - 1;
                        newMessages[lastIndex] = {
                            ...newMessages[lastIndex],
                            content: newMessages[lastIndex].content + chunk
                        };
                        return newMessages;
                    });
                }
            }
        } catch (e) {
            console.error("Chat error:", e);
            setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I'm having trouble connecting to the preview server." }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={cn(
            "flex flex-col bg-white border rounded-lg overflow-hidden shadow-sm transition-all duration-500 ease-in-out",
            isTheaterMode ? "fixed inset-4 z-[100] h-auto" : "h-[600px]",
            unavailable && "bg-slate-50/50 border-dashed border-2"
        )}>
            {/* Header */}
            <div
                className="p-4 flex items-center justify-between text-white shrink-0"
                style={{ backgroundColor: formData.accentColor }}
            >
                <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-full bg-white flex items-center justify-center overflow-hidden border border-white/20">
                        {formData.useTavusAvatar && formData.avatarUrl && formData.avatarUrl.startsWith('http') && !headerImgError ? (
                            (formData.avatarUrl.toLowerCase().includes('.mp4') || formData.avatarUrl.toLowerCase().includes('video') || formData.avatarUrl.toLowerCase().includes('idling')) ? (
                                <video
                                    src={formData.avatarUrl}
                                    className="h-full w-full object-cover"
                                    autoPlay
                                    loop
                                    muted
                                    playsInline
                                    onError={async () => {
                                        console.warn("Header video failed to load: " + formData.avatarUrl);
                                        // Attempt to refresh if it looks like an Anam URL
                                        if (formData.avatarUrl?.includes('anam') || formData.avatarUrl?.includes('cloudflarestorage')) {
                                            try {
                                                const idToUse = agentId || (formData as any).id;
                                                const res = idToUse ? await fetch(`/api/agents/${idToUse}?workspaceId=${workspaceId}`) : null;
                                                if (res && res.ok) {
                                                    const refreshedData = await res.json();
                                                    if (refreshedData.avatarUrl !== formData.avatarUrl && setFormData) {
                                                        setFormData(prev => ({ ...prev, avatarUrl: refreshedData.avatarUrl }));
                                                        return;
                                                    }
                                                }
                                            } catch (e) {
                                                console.error("Failed to refresh avatar URL", e);
                                            }
                                        }
                                        setHeaderImgError(true);
                                    }}
                                />
                            ) : (
                                <img
                                    src={formData.avatarUrl}
                                    alt="Avatar"
                                    className="h-full w-full object-cover"
                                    onError={() => setHeaderImgError(true)}
                                />
                            )
                        ) : (formData.widgetIconUrl && !imgError) ? (
                            <img
                                src={formData.widgetIconUrl}
                                alt="Widget Icon"
                                className="h-full w-full object-contain"
                                onError={() => setImgError(true)}
                            />
                        ) : (
                            <span className="text-xs font-bold text-gray-800">{formData.avatar || (formData.name ? formData.name.substring(0, 2).toUpperCase() : 'AI')}</span>
                        )}
                    </div>
                    <div>
                        <p className="font-semibold text-sm leading-none mb-1">{formData.name || "Agent"}</p>
                        <p className="text-xs opacity-90 leading-none">{formData.primaryFunction || "Assistant"}</p>
                    </div>
                </div>
                <div className="flex gap-1">
                    {/* === CHAT MODE: Always show Switch buttons === */}
                    {mode === 'chat' && !unavailable && (
                        <>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-white hover:bg-white/20 rounded-full"
                                onClick={() => handleModeSwitch('voice')}
                                title="Switch to Voice"
                            >
                                <Phone className="h-4 w-4" />
                            </Button>
                            
                            <Button
                                variant="ghost"
                                size="icon"
                                className={cn(
                                    "h-8 w-8 text-white rounded-full transition-all",
                                    (!formData.useTavusAvatar || !(formData.tavusReplicaId || formData.anamPersonaId)) ? "opacity-60 bg-white/5 border border-white/10" : "hover:bg-white/20 bg-white/10"
                                )}
                                onClick={() => {
                                    if (!formData.useTavusAvatar) {
                                        toast.info("Please enable Visual Presence in Step 2 to use the avatar");
                                        return;
                                    }
                                    if (!(formData.tavusReplicaId || formData.anamPersonaId)) {
                                        toast.error("Please select a specific avatar in the 'Choose Your Avatar' section first.");
                                        return;
                                    }
                                    handleModeSwitch('avatar');
                                }}
                                title={!formData.useTavusAvatar ? "Enable Visual Presence to use Avatar" : (!(formData.tavusReplicaId || formData.anamPersonaId) ? "Select an avatar below first" : "Switch to Avatar")}
                            >
                                <Video className="h-4 w-4" />
                            </Button>
                        </>
                    )}

                    {/* === VOICE MODE: Show Chat + Avatar switch buttons === */}
                    {mode === 'voice' && !unavailable && (
                        <>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-white hover:bg-white/20 rounded-full"
                                onClick={handleEndCall}
                                title="Switch to Chat"
                            >
                                <MessageSquare className="h-4 w-4" />
                            </Button>
                            {(formData.tavusReplicaId || formData.anamPersonaId) && (
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 text-white hover:bg-white/20 rounded-full"
                                    onClick={() => handleModeSwitch('avatar')}
                                    title="Switch to Avatar"
                                >
                                    <Video className="h-4 w-4" />
                                </Button>
                            )}
                        </>
                    )}

                    {/* === AVATAR MODE: Show Chat + Voice switch buttons + theater === */}
                    {mode === 'avatar' && !unavailable && (
                        <>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-white hover:bg-white/20 rounded-full"
                                onClick={handleEndCall}
                                title="Switch to Chat"
                            >
                                <MessageSquare className="h-4 w-4" />
                            </Button>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-white hover:bg-white/20 rounded-full"
                                onClick={() => handleModeSwitch('voice')}
                                title="Switch to Voice"
                            >
                                <Phone className="h-4 w-4" />
                            </Button>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-white hover:bg-white/20 rounded-full"
                                onClick={() => setIsTheaterMode(!isTheaterMode)}
                                title={isTheaterMode ? "Exit Theater Mode" : "Expand Window"}
                            >
                                {isTheaterMode ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                            </Button>
                        </>
                    )}

                    {/* Theater mode for chat when already expanded */}
                    {mode === 'chat' && isTheaterMode && !unavailable && (
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-white hover:bg-white/20 rounded-full"
                            onClick={() => setIsTheaterMode(false)}
                            title="Exit Theater Mode"
                        >
                            <Minimize2 className="h-4 w-4" />
                        </Button>
                    )}
                </div>
            </div>

            {/* Content */}
            {unavailable ? (
                <div className="flex-1 flex items-center justify-center p-8 bg-slate-50/50">
                    <CardContent className="flex flex-col items-center text-center p-0">
                        <div className="h-16 w-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                            <Bot className="h-8 w-8 text-slate-300" />
                        </div>
                        <h3 className="font-bold text-slate-700 mb-2">Preview Unavailable</h3>
                        <p className="text-sm text-slate-500 max-w-[200px]">
                            Complete the configuration steps to reach the Live Preview in Step 6.
                        </p>
                    </CardContent>
                </div>
            ) : mode === 'chat' ? (
                <>
                    <div className="flex-1 p-4 bg-gray-50/50 overflow-y-auto" ref={scrollRef}>
                        <div className="space-y-4 max-w-3xl mx-auto">
                            {messages.map((m, i) => (
                                <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    {m.role === 'assistant' && (
                                        <div className="w-8 h-8 rounded-full bg-white border flex items-center justify-center shrink-0 overflow-hidden">
                                            {formData.useTavusAvatar && formData.avatarUrl && !imgError ? (
                                                formData.avatarUrl && formData.avatarUrl.includes('.mp4') ? (
                                                    <video
                                                        src={formData.avatarUrl}
                                                        className="w-full h-full object-cover"
                                                        autoPlay
                                                        loop
                                                        muted
                                                        playsInline
                                                        onError={() => {
                                                            console.warn("Message video failed to load: " + formData.avatarUrl);
                                                            setImgError(true);
                                                        }}
                                                    />
                                                ) : (
                                                    <img
                                                        src={formData.avatarUrl}
                                                        alt="Bot"
                                                        className="w-full h-full object-cover"
                                                        onError={(e) => {
                                                            e.currentTarget.style.display = 'none';
                                                            setImgError(true);
                                                        }}
                                                    />
                                                )
                                            ) : (!formData.useTavusAvatar && formData.widgetIconUrl && !imgError) ? (
                                                <img
                                                    src={formData.widgetIconUrl}
                                                    alt="Bot Icon"
                                                    className="w-full h-full object-contain"
                                                    onError={(e) => {
                                                        e.currentTarget.style.display = 'none';
                                                        setImgError(true);
                                                    }}
                                                />
                                            ) : (
                                                <Bot className="h-5 w-5 text-gray-400" />
                                            )}
                                        </div>
                                    )}
                                    <div
                                        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm shadow-sm ${m.role === 'user'
                                            ? 'text-white'
                                            : 'bg-white border text-gray-800'
                                            }`}
                                        style={m.role === 'user' ? { backgroundColor: formData.accentColor } : {}}
                                    >
                                        {m.role === 'user' ? (
                                            m.content
                                        ) : (
                                            <div className="prose prose-sm max-w-none break-words prose-p:leading-relaxed prose-pre:p-0">
                                                <Markdown
                                                    options={{
                                                        overrides: {
                                                            a: {
                                                                component: ({ children, ...props }: React.HTMLProps<HTMLAnchorElement>) => (
                                                                    <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline font-medium break-all">
                                                                        {children}
                                                                    </a>
                                                                )
                                                            }
                                                        }
                                                    }}
                                                >
                                                    {m.content}
                                                </Markdown>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {/* Typing indicator */}
                            {isLoading && (
                                <div className="flex justify-start">
                                    <div className="bg-white border rounded-2xl px-4 py-2.5 shadow-sm">
                                        <div className="flex gap-1">
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="p-4 border-t bg-white shrink-0">
                        <form
                            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                            className="flex gap-2"
                        >
                            <Input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Type a message..."
                                className="flex-1"
                            />
                            <Button type="submit" size="icon" style={{ backgroundColor: formData.accentColor }}>
                                <Send className="h-4 w-4" />
                            </Button>
                        </form>
                        {!formData.removeBranding && (
                            <div className="text-center mt-3">
                                <span className="text-[10px] text-gray-400 font-medium">Powered by SupaAgent</span>
                            </div>
                        )}
                    </div>
                </>
            ) : (
                <div className="flex-1 bg-white relative">
                    {(token && url) ? (
                        <LiveKitRoom
                            key={`${token}-${mode}-${formData.tavusReplicaId || formData.anamPersonaId}`}
                            token={token}
                            serverUrl={url}
                            connect={!!token}
                            audio={true}
                            video={mode === 'avatar'}
                            className="flex flex-col h-full w-full"
                            onConnected={handleConnected}
                            onDisconnected={handleDisconnected}
                        >
                            {/* Reconnecting Overlay */}
                            <AnimatePresence>
                                {connectionStatus === 'reconnecting' && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        className="absolute inset-0 z-50 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm flex flex-col items-center justify-center gap-3"
                                    >
                                        <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent" />
                                        <p className="text-sm font-medium text-muted-foreground">Reconnecting...</p>
                                        <p className="text-xs text-muted-foreground/70">Attempt {reconnectAttempts.current}/{MAX_RECONNECT_ATTEMPTS}</p>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                            {connectionStatus === 'error' && (
                                <div className="absolute inset-0 z-50 bg-white flex flex-col items-center justify-center gap-4 p-6 text-center">
                                    <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
                                        <X className="h-8 w-8 text-red-500" />
                                    </div>
                                    <h3 className="font-semibold text-lg">Connection Lost</h3>
                                    <p className="text-sm text-muted-foreground">Unable to reconnect after multiple attempts.</p>
                                    <div className="flex gap-2">
                                        <Button onClick={handleRetry} variant="default" size="sm">
                                            <RefreshCw className="h-4 w-4 mr-2" />
                                            Retry
                                        </Button>
                                        <Button onClick={handleEndCall} variant="outline" size="sm">Go Back</Button>
                                    </div>
                                </div>
                            )}
                            {mode === 'avatar' ? (
                                <div className="flex-1 relative bg-slate-50 overflow-hidden group">
                                    <AvatarVideoStage
                                        formData={formData}
                                        pipSize={pipSize}
                                        setPipSize={setPipSize}
                                        onClose={handleEndCall}
                                        showCaptions={showCaptions}
                                        setShowCaptions={setShowCaptions}
                                    />
                                </div>
                            ) : (
                                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center min-h-0 bg-white">
                                    <div className="flex-1 flex flex-col items-center justify-center gap-2 w-full">
                                        <div className="relative w-48 h-48 flex items-center justify-center">
                                            <CustomVisualizer accentColor={formData.accentColor} />
                                        </div>

                                        <div className="space-y-1 w-full">
                                            <VoiceStatusDisplay name={formData.name || "Agent"} />
                                        </div>
                                    </div>

                                    <div className="w-full max-w-xs space-y-3 shrink-0 mb-4 z-10">
                                        <VoiceControlPanel onClose={handleEndCall} />
                                    </div>
                                </div>
                            )}
                            <RoomAudioRenderer />
                            <ParticipantLogger />
                        </LiveKitRoom>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                            {(error || connectionStatus === 'error') ? (
                                <div className="text-red-500 space-y-4">
                                    <p className="font-semibold">Connection Failed</p>
                                    <p className="text-sm text-gray-500">{error || "The connection was lost. Please try again."}</p>
                                    <div className="flex gap-2 justify-center">
                                        <Button onClick={handleRetry} variant="default" size="sm">Retry</Button>
                                        <Button onClick={handleEndCall} variant="outline" size="sm">Go Back</Button>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-4 animate-pulse">
                                    <div className="h-24 w-24 rounded-full bg-gray-100 mx-auto" />
                                    <p className="text-sm text-gray-400">Connecting to voice server...</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function TranscriptOverlay({ showCaptions }: { showCaptions: boolean }) {
    const { state } = useVoiceAssistant();
    const segments = useTranscriptions();
    const [messages, setMessages] = useState<any[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (segments && segments.length > 0) {
            setMessages(prev => {
                const newMessages = [...prev];
                (segments as any[]).forEach(seg => {
                    const existingIdx = newMessages.findIndex(m => m.id === seg.id);
                    if (existingIdx !== -1) {
                        newMessages[existingIdx] = { ...newMessages[existingIdx], text: seg.text, timestamp: Date.now() };
                    } else {
                        newMessages.push({
                            id: seg.id,
                            text: seg.text,
                            timestamp: Date.now()
                        });
                    }
                });
                // Keep last 8 messages within 15 seconds for better readability
                return newMessages
                    .filter(m => Date.now() - m.timestamp < 15000)
                    .slice(-8);
            });
        }
    }, [segments]);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({
                top: scrollRef.current.scrollHeight,
                behavior: 'smooth'
            });
        }
    }, [messages]);

    // Secondary cleaner to remove stale messages
    useEffect(() => {
        const interval = setInterval(() => {
            setMessages(prev => prev.filter(m => Date.now() - m.timestamp < 15000));
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    if (!showCaptions) return null;

    return (
        <div ref={scrollRef} className="absolute bottom-24 left-0 right-0 z-50 flex flex-col items-center justify-end px-6 pointer-events-none gap-2 overflow-y-auto max-h-[35%] scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
            <AnimatePresence mode="popLayout">
                {messages.map((m) => (
                    <motion.div
                        key={m.id}
                        layout
                        initial={{ opacity: 0, y: 20, scale: 0.9 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -60, scale: 0.8, transition: { duration: 0.4 } }}
                        className="bg-black/60 backdrop-blur-md px-5 py-2.5 rounded-2xl text-white text-sm md:text-base font-medium shadow-xl border border-white/10 max-w-[90%] text-center"
                    >
                        {m.text}
                    </motion.div>
                ))}
            </AnimatePresence>

            <AnimatePresence>
                {messages.length === 0 && state === 'thinking' && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        className="bg-blue-600/80 backdrop-blur-md px-4 py-1.5 rounded-full text-white text-[10px] uppercase tracking-wider font-bold shadow-lg border border-blue-400/30 mb-2"
                    >
                        Thinking...
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

function CustomControls({ onClose, showCaptions, toggleCaptions }: { onClose: () => void, showCaptions?: boolean, toggleCaptions?: () => void }) {
    const { toggle: toggleMic, enabled: isMicEnabled } = useTrackToggle({ source: Track.Source.Microphone });
    const { toggle: toggleCam, enabled: isCamEnabled } = useTrackToggle({ source: Track.Source.Camera });

    const isMuted = !isMicEnabled;
    const isVideoOff = !isCamEnabled;

    // Since LiveKit's deep components might auto-enable the track on launch,
    // we strictly monitor the TRUE track state and force it down once on connect.
    // [STABILIZATION]: User story now requires mic/camera ON by default.
    // Removed force-disarm logic to allow immediate interaction.

    return (
        <div className="flex items-center gap-3 p-2 rounded-full bg-white/80 dark:bg-black/60 backdrop-blur-md border border-slate-200 dark:border-white/10 shadow-2xl">
            <Button
                variant={showCaptions ? "secondary" : "secondary"}
                size="icon"
                className={`rounded-full h-10 w-10 shrink-0 ${!showCaptions ? 'text-slate-400' : ''}`}
                onClick={toggleCaptions}
                title={showCaptions ? "Hide Captions" : "Show Captions"}
            >
                {showCaptions ? <MessageSquare className="h-4 w-4" /> : <MessageSquareOff className="h-4 w-4" />}
            </Button>
            <div className="w-px h-6 bg-slate-200 dark:bg-white/20 mx-1" />
            <Button
                variant={isMuted ? "destructive" : "secondary"}
                size="icon"
                className="rounded-full h-10 w-10 shrink-0"
                onClick={() => toggleMic()}
            >
                {isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </Button>
            <Button
                variant={isVideoOff ? "destructive" : "secondary"}
                size="icon"
                className="rounded-full h-10 w-10 shrink-0"
                onClick={() => toggleCam()}
                title={isVideoOff ? "Resume Vision" : "Pause Vision"}
            >
                {isVideoOff ? <CameraOff className="h-4 w-4" /> : <Camera className="h-4 w-4" />}
            </Button>
            <div className="w-px h-6 bg-slate-200 dark:bg-white/20 mx-1" />
            <Button
                variant="destructive"
                size="icon"
                className="rounded-full h-10 w-10 shrink-0"
                onClick={onClose}
            >
                <Phone className="h-4 w-4 rotate-[135deg]" />
            </Button>
        </div>
    );
}

function VoiceStatusDisplay({ name }: { name: string }) {
    // ... (rest remains same)
    const { state } = useVoiceAssistant();
    const connectionState = useConnectionState();
    const { localParticipant } = useLocalParticipant();
    const participants = useParticipants();
    const [agentStuck, setAgentStuck] = useState(false);

    useEffect(() => {
        console.log("DEBUG: [agentId] VoiceStatusDisplay state update", {
            connectionState,
            assistantState: state,
            participantCount: participants.length,
            participants: participants.map((p: any) => ({ identity: p.identity, name: p.name, metadata: p.metadata })),
            localMic: localParticipant?.isMicrophoneEnabled
        });
    }, [connectionState, state, participants, localParticipant]);

    // STABILITY FIX: Detect when agent joins room but never transitions to a working state.
    // This catches the silent Gemini crash / file-watcher race condition.
    useEffect(() => {
        if (state === 'connecting' && String(connectionState).toLowerCase() === 'connected') {
            const timeout = setTimeout(() => {
                console.error("⏰ [STUCK DETECTION] Agent joined room but never started after 45s. Possible cold start or silent crash.");
                setAgentStuck(true);
            }, 45000);
            return () => clearTimeout(timeout);
        } else {
            setAgentStuck(false);
        }
    }, [state, connectionState]);

    let statusText = "Connecting...";
    let statusColor = "bg-yellow-500";
    let subText = "Waiting for agent...";

    const currentRoomState = String(connectionState).toLowerCase();

    if (currentRoomState === "connected") {
        if (localParticipant && !localParticipant.isMicrophoneEnabled) {
            statusText = "Microphone Muted";
            statusColor = "bg-red-500";
        } else {
            switch (state) {
                case "connecting":
                    statusText = agentStuck ? "Agent Not Responding" : "Connecting...";
                    statusColor = agentStuck ? "bg-orange-500" : "bg-yellow-500";
                    subText = agentStuck ? "Try ending the call and starting again" : "Agent is joining...";
                    break;
                case "listening":
                    statusText = "Listening...";
                    statusColor = "bg-green-500";
                    subText = "Speak now...";
                    break;
                case "thinking":
                    statusText = "Thinking...";
                    statusColor = "bg-purple-500";
                    subText = "Agent is processing...";
                    break;
                case "speaking":
                    statusText = "Speaking...";
                    statusColor = "bg-blue-500";
                    subText = "Agent is speaking...";
                    break;
                default:
                    statusText = "Ready";
                    statusColor = "bg-green-500";
            }
        }
    } else if (currentRoomState === "connecting" || currentRoomState === "reconnecting") {
        statusText = "Connecting...";
        statusColor = "bg-yellow-500";
    } else {
        statusText = "Disconnected";
        statusColor = "bg-red-500";
    }

    return (
        <>
            <h3 className="font-semibold text-lg">{name}</h3>
            <div className="flex items-center gap-2 justify-center mt-1">
                <div className={cn("w-2 h-2 rounded-full animate-pulse", statusColor)} />
                <p className="text-sm text-muted-foreground transition-all duration-300">{statusText}</p>
            </div>
            {agentStuck && (
                <p className="text-xs text-orange-500 mt-1">Agent may have crashed during startup. Try ending the call.</p>
            )}
        </>
    );
}

function CustomVisualizer({ accentColor }: { accentColor: string }) {
    const { state, audioTrack } = useVoiceAssistant();

    return (
        <div className="w-full h-full flex items-center justify-center">
            <AgentAudioVisualizerAura
                state={state}
                size="lg"
                color={(accentColor || "#6D28D9") as `#${string}`}
                colorShift={0.4}
                themeMode="light"
                className="aspect-square w-full max-w-[200px]"
            />
        </div>
    );
}

function VoiceControlPanel({ onClose, onDisconnect, isVideo, showCaptions, toggleCaptions }: { onClose: () => void; onDisconnect?: () => void; isVideo?: boolean; showCaptions?: boolean; toggleCaptions?: () => void }) {
    const { toggle: toggleMic, enabled: isMicEnabled } = useTrackToggle({ source: Track.Source.Microphone });
    
    const isMuted = !isMicEnabled;

    // Handle End Call - immediately stop tracks via toggle if on
    const handleEndCall = async () => {
        try {
            if (isMicEnabled) {
                toggleMic();
            }
            if (onDisconnect) {
                onDisconnect();
            }
        } catch (e) {
            console.error("Error during disconnect:", e);
        }
        onClose();
    };

    // Force disarm on initial active state
    // [STABILIZATION]: User story now requires mic ON by default.
    // Removed force-disarm logic to allow immediate interaction.

    return (
        <div className="flex flex-col gap-3 w-full items-center">
            <Button
                variant={isMuted ? "destructive" : "secondary"}
                className={`w-40 rounded-full shadow-md ${isMuted ? 'bg-red-100 text-red-600 hover:bg-red-200 border-red-200' : 'bg-white hover:bg-gray-100 border'}`}
                onClick={() => toggleMic()}
            >
            {isMuted ? (
                    <>
                        <MicOff className="h-4 w-4 mr-2" />
                        Unmute
                    </>
                ) : (
                    <>
                        <Mic className="h-4 w-4 mr-2" />
                        Mute
                    </>
                )}
            </Button>
            <Button
                variant="destructive"
                className="w-40 rounded-full shadow-md"
                onClick={handleEndCall}
            >
                End Call
            </Button>

            <Button
                variant="ghost"
                size="sm"
                className="w-40 text-muted-foreground"
                onClick={onClose}
            >
                Switch to Chat
            </Button>
        </div>
    );
}

function AvatarVideoStage({ formData, onClose, pipSize, setPipSize, showCaptions, setShowCaptions }: { formData: any; onClose: () => void; pipSize: 'sm' | 'md' | 'lg'; setPipSize: (s: 'sm' | 'md' | 'lg') => void; showCaptions: boolean; setShowCaptions: (v: boolean) => void }) {
    const tracks = useTracks([Track.Source.Camera]);
    // Filter for remote camera (the avatar)
    const remoteTrack = tracks.find(t => t.participant.isLocal === false && t.source === Track.Source.Camera);
    // Filter for local camera (user preview)
    const localTrack = tracks.find(t => t.participant.isLocal === true && t.source === Track.Source.Camera);

    return (
        <div className="w-full h-full relative bg-slate-50 dark:bg-zinc-900 flex items-center justify-center">
            {!(formData.tavusReplicaId || formData.anamPersonaId) ? (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 p-8 text-center">
                    <div className="w-16 h-16 bg-amber-100 rounded-2xl flex items-center justify-center mb-4 text-amber-600">
                        <AlertTriangle className="h-8 w-8" />
                    </div>
                    <span className="text-sm font-semibold text-slate-800 mb-1">No Avatar Selected</span>
                    <p className="text-xs text-slate-500 max-w-[200px]">
                        Please select an avatar in Step 2 to enable video calls.
                    </p>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="mt-4 text-primary"
                        onClick={onClose}
                    >
                        Go Back
                    </Button>
                </div>
            ) : remoteTrack ? (
                <VideoTrack trackRef={remoteTrack} className="w-full h-full object-cover" />
            ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 animate-pulse">
                    <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mb-4 text-blue-600">
                        <Bot className="h-8 w-8 text-blue-600" />
                    </div>
                    <span className="text-sm font-medium">Connecting to Avatar...</span>
                </div>
            )}

            {/* PIP Self View */}
            {localTrack && (
                <div
                    className={cn(
                        "absolute top-4 right-4 bg-black rounded-xl overflow-hidden border border-white/20 shadow-2xl z-20 transition-all duration-300 group/pip",
                        pipSize === 'sm' ? "w-24 h-32" :
                            pipSize === 'md' ? "w-36 h-48" :
                                "w-52 h-72"
                    )}
                >
                    <VideoTrack trackRef={localTrack} className="w-full h-full object-cover mirror" />

                    {/* PIP Size Controls - Visible on PIP hover */}
                    <div className="absolute bottom-2 left-0 right-0 flex justify-center opacity-0 group-hover/pip:opacity-100 transition-opacity gap-1 px-2">
                        <button
                            onClick={(e) => { e.stopPropagation(); setPipSize('sm'); }}
                            className={cn("p-1 rounded-md bg-black/60 text-white hover:bg-white/20", pipSize === 'sm' && "text-blue-400")}
                            title="Small PIP"
                        >
                            <Square className="w-3 h-3" />
                        </button>
                        <button
                            onClick={(e) => { e.stopPropagation(); setPipSize('md'); }}
                            className={cn("p-1 rounded-md bg-black/60 text-white hover:bg-white/20", pipSize === 'md' && "text-blue-400")}
                            title="Medium PIP"
                        >
                            <Layout className="w-3 h-3" />
                        </button>
                        <button
                            onClick={(e) => { e.stopPropagation(); setPipSize('lg'); }}
                            className={cn("p-1 rounded-md bg-black/60 text-white hover:bg-white/20", pipSize === 'lg' && "text-blue-400")}
                            title="Large PIP"
                        >
                            <Monitor className="w-3 h-3" />
                        </button>
                    </div>
                </div>
            )}

            {/* Live Transcript Overlay */}
            <div className="absolute bottom-4 left-4 right-4 z-30 pointer-events-none">
                <TranscriptOverlay showCaptions={showCaptions} />
            </div>

            {/* Floating Controls */}
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-auto">
                <CustomControls onClose={onClose} showCaptions={showCaptions} toggleCaptions={() => setShowCaptions(!showCaptions)} />
            </div>
        </div>
    );
}

function ParticipantLogger() {
    const remoteParticipants = useParticipants();
    const { localParticipant } = useLocalParticipant();
    
    useEffect(() => {
        const total = remoteParticipants.length + (localParticipant ? 1 : 0);
        console.log(`🚀 [PARTICIPANT COUNT] Total: ${total} (Remote: ${remoteParticipants.length}, Local: ${localParticipant ? 1 : 0})`);
        
        // Log individual identities to help identify "ghost" participants
        remoteParticipants.forEach(p => {
            const isAgent = p.attributes?.agent === 'true';
            const state = p.attributes?.['lk.agent.state'] || 'unknown';
            console.log(`👥 Remote: ${p.identity} (Agent: ${isAgent}, State: ${state}, Sid: ${p.sid})`);
        });
        if (localParticipant) {
            console.log(`👤 Local: ${localParticipant.identity} (Sid: ${localParticipant.sid})`);
        }
    }, [remoteParticipants.length, localParticipant]);
    
    return null;
}
