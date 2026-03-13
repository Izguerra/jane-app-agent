"use client";

import {
    LiveKitRoom,
    RoomAudioRenderer,
    BarVisualizer,
    useVoiceAssistant,
    VoiceAssistantControlBar,
    useConnectionState,
    useLocalParticipant,
    ConnectionState,
    useTracks,
    VideoTrack,
    TrackReference,
} from "@livekit/components-react";
import { Track } from "livekit-client";
import "@livekit/components-styles";
import { useEffect, useState, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Phone, X, MessageCircle, Send, User, Bot, ChevronDown, Video, Mic, MicOff, Camera, CameraOff, Upload, Maximize2, Minimize2, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { ChatSession } from "@/components/chat-session";

type WidgetMode = 'chat' | 'voice' | 'avatar';
type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'transitioning' | 'error';

const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_DELAY_MS = 2000;
const RECONNECT_TIMEOUT_MS = 15000;

export function VoiceWidget() {
    const [isOpen, setIsOpen] = useState(false);
    const [mode, setMode] = useState<WidgetMode>('chat');
    const [settings, setSettings] = useState<any>(null);

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await fetch('/api/public/active-agent-settings');
                if (res.ok) {
                    const data = await res.json();
                    setSettings(data);
                }
            } catch (e) {
                console.error("Failed to fetch agent settings", e);
            }
        };
        if (isOpen) {
            fetchSettings();
        }
    }, [isOpen]);
    const [isFullScreen, setIsFullScreen] = useState(false);

    // Reset full screen on close
    useEffect(() => {
        if (!isOpen) setIsFullScreen(false);
    }, [isOpen]);

    const handleModeSwitch = async (targetMode: WidgetMode) => {
        if (mode === targetMode) return;

        if ((mode === 'voice' || mode === 'avatar') && (targetMode === 'voice' || targetMode === 'avatar')) {
            await toast.promise(
                new Promise(async (resolve) => {
                    setMode('chat'); // Temporarily drop to chat to force unmount
                    await new Promise(r => setTimeout(r, 2500));
                    setMode(targetMode);
                    resolve(true);
                }),
                {
                    loading: `Switching to ${targetMode}...`,
                    success: `${targetMode.charAt(0).toUpperCase() + targetMode.slice(1)} mode ready`,
                    error: 'Transition failed',
                }
            );
            return;
        }
        
        setMode(targetMode);
    };

    return (
        <div className={cn(
            "fixed z-50 flex flex-col items-end gap-4 transition-all duration-300",
            isFullScreen ? "inset-4" : "bottom-6 right-6"
        )}>
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 20, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className={cn(
                            "bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-border overflow-hidden flex flex-col origin-bottom-right transition-all duration-300",
                            isFullScreen ? "w-full h-full" : "w-[380px] h-[600px]"
                        )}
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between p-4 border-b bg-white dark:bg-zinc-900 z-10 relative shadow-sm">
                            <div className="flex items-center gap-2">
                                <div className="relative">
                                    <div className={cn("w-2.5 h-2.5 rounded-full animate-pulse", mode === 'avatar' ? 'bg-purple-500' : 'bg-green-500')} />
                                    <div className={cn("absolute inset-0 rounded-full animate-ping opacity-50", mode === 'avatar' ? 'bg-purple-500' : 'bg-green-500')} />
                                </div>
                                <span className="font-semibold text-sm">SupaAgent AI</span>
                            </div>
                            <div className="flex items-center gap-1">
                                {mode === 'chat' && (
                                    <>
                                        {!settings?.use_tavus_avatar && (
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8 rounded-full text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950/30"
                                                onClick={() => handleModeSwitch('voice')}
                                                title="Start Voice Call"
                                            >
                                                <Phone className="h-4 w-4" />
                                            </Button>
                                        )}
                                        {settings?.use_tavus_avatar && (
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8 rounded-full text-purple-500 hover:bg-purple-50 dark:hover:bg-purple-950/30"
                                                onClick={() => handleModeSwitch('avatar')}
                                                title="Start Video Call"
                                            >
                                                <Video className="h-4 w-4" />
                                            </Button>
                                        )}
                                    </>
                                )}
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 rounded-full hover:bg-secondary hidden sm:flex"
                                    onClick={() => setIsFullScreen(!isFullScreen)}
                                >
                                    {isFullScreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 rounded-full hover:bg-secondary"
                                    onClick={() => setIsOpen(false)}
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>

                        {/* Content Area */}
                        <div className="flex-1 relative overflow-hidden bg-gray-50 dark:bg-zinc-950/50">
                            <AnimatePresence mode="wait">
                                {mode === 'chat' ? (
                                    <motion.div
                                        key="chat"
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -20 }}
                                        className="absolute inset-0"
                                    >
                                        <ChatSession embedded={true} />
                                    </motion.div>
                                ) : mode === 'voice' ? (
                                    <motion.div
                                        key="voice"
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: 20 }}
                                        className="absolute inset-0 bg-white dark:bg-zinc-900"
                                    >
                                        <VoiceSession onClose={() => setMode('chat')} mode="voice" />
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="avatar"
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        className="absolute inset-0 bg-white"
                                    >
                                        <AvatarSession onClose={() => setMode('chat')} />
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {!isFullScreen && (
                <Button
                    onClick={() => setIsOpen(!isOpen)}
                    size="icon"
                    className={cn(
                        "h-14 w-14 rounded-full shadow-lg transition-all duration-300 hover:scale-105",
                        isOpen ? "rotate-0 bg-destructive hover:bg-destructive/90" : "bg-primary hover:bg-primary/90"
                    )}
                >
                    {isOpen ? (
                        <ChevronDown className="h-6 w-6" />
                    ) : (
                        <MessageCircle className="h-6 w-6" />
                    )}
                </Button>
            )}
        </div>
    );
}

// --- Voice Only Session (with Reconnection Guard) ---
export function VoiceSession({ onClose, mode = "voice" }: { onClose: () => void; mode?: string }) {
    const { token, url, error, isConnecting, refresh } = useTokenFetch(mode);
    const intentionalDisconnect = useRef(false);
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('idle');
    const reconnectAttempts = useRef(0);
    const reconnectTimer = useRef<NodeJS.Timeout | null>(null);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
        };
    }, []);

    const handleDisconnected = useCallback(() => {
        console.log("DEBUG: VoiceSession onDisconnected", { intentional: intentionalDisconnect.current, attempts: reconnectAttempts.current });

        // If user intentionally ended the call, go back to chat
        if (intentionalDisconnect.current) {
            intentionalDisconnect.current = false;
            setConnectionStatus('idle');
            onClose();
            return;
        }

        // Otherwise, attempt reconnection
        if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
            console.log("DEBUG: Max reconnect attempts reached, reverting to chat");
            setConnectionStatus('error');
            return;
        }

        setConnectionStatus('reconnecting');
        reconnectAttempts.current += 1;

        reconnectTimer.current = setTimeout(() => {
            console.log(`DEBUG: Reconnection attempt ${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS}`);
            refresh(); // Fetch a new token and reconnect
        }, RECONNECT_DELAY_MS);
    }, [onClose, refresh]);

    const handleEndCall = useCallback(() => {
        intentionalDisconnect.current = true;
        onClose();
    }, [onClose]);

    const handleRetry = useCallback(() => {
        reconnectAttempts.current = 0;
        setConnectionStatus('connecting');
        refresh();
    }, [refresh]);

    // Reset reconnect counter on successful connection
    const handleConnected = useCallback(() => {
        console.log("DEBUG: VoiceSession connected successfully");
        reconnectAttempts.current = 0;
        setConnectionStatus('connected');
    }, []);

    if (error && connectionStatus !== 'reconnecting') return <ErrorDisplay error={error} onClose={onClose} />;
    if (isConnecting && connectionStatus !== 'reconnecting') return <LoadingDisplay />;
    if (!token && connectionStatus !== 'reconnecting') return <LoadingDisplay />;

    // Show error state with retry option
    if (connectionStatus === 'error') {
        return (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 text-center p-6 bg-white dark:bg-zinc-900">
                <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                    <X className="h-8 w-8 text-red-500" />
                </div>
                <div className="space-y-2">
                    <h3 className="font-semibold text-lg">Connection Lost</h3>
                    <p className="text-sm text-muted-foreground">Unable to reconnect after multiple attempts.</p>
                </div>
                <div className="flex gap-2">
                    <Button onClick={handleRetry} variant="default" size="sm">
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Retry
                    </Button>
                    <Button onClick={onClose} variant="outline" size="sm">Go Back</Button>
                </div>
            </div>
        );
    }

    return (
        <LiveKitRoom
            token={token}
            serverUrl={url}
            connect={!!token}
            audio={true}
            video={false}
            className="flex flex-col h-full w-full bg-white dark:bg-zinc-900"
            onDisconnected={handleDisconnected}
            onConnected={handleConnected}
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

            <div className="flex-1 flex flex-col items-center justify-center p-4 overflow-hidden min-h-0">
                <div className="relative w-32 h-32 flex items-center justify-center mb-4">
                    <div className="absolute inset-0 bg-blue-500/10 rounded-full animate-[pulse_3s_ease-in-out_infinite]" />
                    <div className="absolute inset-4 bg-blue-500/20 rounded-full animate-[pulse_2s_ease-in-out_infinite]" />
                    <div className="relative z-10 w-24 h-24 bg-gradient-to-b from-blue-500 to-blue-600 rounded-full shadow-xl flex items-center justify-center text-white ring-4 ring-white dark:ring-zinc-900">
                        <Phone className="h-10 w-10" />
                    </div>
                </div>
                <SimpleVoiceVisualizer />
                <AgentStatusDisplay />
            </div>

            <div className="p-2 bg-secondary/10 border-t">
                <div className="flex flex-col gap-2">
                    <VoiceAssistantControlBar controls={{ leave: false }} />
                    <Button onClick={handleEndCall} variant="destructive" className="w-full rounded-full shadow-sm">
                        End Call
                    </Button>
                </div>
            </div>
            <RoomAudioRenderer />
        </LiveKitRoom>
    );
}

// --- Avatar Video Session (with Reconnection Guard) ---
export function AvatarSession({ onClose }: { onClose: () => void }) {
    const { token, url, error, isConnecting, refresh } = useTokenFetch("avatar");
    const intentionalDisconnect = useRef(false);
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('idle');
    const reconnectAttempts = useRef(0);
    const reconnectTimer = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        return () => {
            if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
        };
    }, []);

    const handleDisconnected = useCallback(() => {
        console.log("DEBUG: AvatarSession onDisconnected", { intentional: intentionalDisconnect.current, attempts: reconnectAttempts.current });

        if (intentionalDisconnect.current) {
            intentionalDisconnect.current = false;
            setConnectionStatus('idle');
            onClose();
            return;
        }

        if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
            setConnectionStatus('error');
            return;
        }

        setConnectionStatus('reconnecting');
        reconnectAttempts.current += 1;

        reconnectTimer.current = setTimeout(() => {
            refresh();
        }, RECONNECT_DELAY_MS);
    }, [onClose, refresh]);

    const handleEndCall = useCallback(() => {
        intentionalDisconnect.current = true;
        onClose();
    }, [onClose]);

    const handleRetry = useCallback(() => {
        reconnectAttempts.current = 0;
        setConnectionStatus('connecting');
        refresh();
    }, [refresh]);

    const handleConnected = useCallback(() => {
        reconnectAttempts.current = 0;
        setConnectionStatus('connected');
    }, []);

    if (error && connectionStatus !== 'reconnecting') return <ErrorDisplay error={error} onClose={onClose} />;
    if (isConnecting && connectionStatus !== 'reconnecting') return <LoadingDisplay />;
    if (!token && connectionStatus !== 'reconnecting') return <LoadingDisplay />;

    if (connectionStatus === 'error') {
        return (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 text-center p-6 bg-white dark:bg-zinc-900">
                <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                    <X className="h-8 w-8 text-red-500" />
                </div>
                <div className="space-y-2">
                    <h3 className="font-semibold text-lg">Connection Lost</h3>
                    <p className="text-sm text-muted-foreground">Unable to reconnect to avatar session.</p>
                </div>
                <div className="flex gap-2">
                    <Button onClick={handleRetry} variant="default" size="sm">
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Retry
                    </Button>
                    <Button onClick={onClose} variant="outline" size="sm">Go Back</Button>
                </div>
            </div>
        );
    }

    return (
        <LiveKitRoom
            token={token}
            serverUrl={url}
            connect={!!token}
            audio={true}
            video={true}
            className="flex flex-col h-full w-full bg-white relative group"
            onDisconnected={handleDisconnected}
            onConnected={handleConnected}
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
                        <div className="animate-spin rounded-full h-8 w-8 border-2 border-purple-500 border-t-transparent" />
                        <p className="text-sm font-medium text-muted-foreground">Reconnecting to Avatar...</p>
                        <p className="text-xs text-muted-foreground/70">Attempt {reconnectAttempts.current}/{MAX_RECONNECT_ATTEMPTS}</p>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main Video Area */}
            <div className="flex-1 relative overflow-hidden flex items-center justify-center">
                <VideoStage />
                {/* Live Transcript Overlay */}
                <div className="absolute bottom-4 left-4 right-4 z-20 pointer-events-none">
                    <TranscriptOverlay />
                </div>
            </div>

            {/* Floating Controls (Visible on hover or mobile) */}
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center gap-3 p-2 rounded-full bg-white/80 dark:bg-black/60 backdrop-blur-md border border-slate-200 dark:border-white/10 shadow-2xl">
                <CustomControls onClose={handleEndCall} />
            </div>

            <RoomAudioRenderer />
        </LiveKitRoom>
    );
}

function VideoStage() {
    const tracks = useTracks([Track.Source.Camera, Track.Source.ScreenShare, Track.Source.Unknown]);

    useEffect(() => {
        console.log("DEBUG: VideoStage Tracks:", tracks.map(t => ({
            sid: t.publication.trackSid,
            kind: t.publication.kind,
            source: t.source,
            isLocal: t.participant.isLocal,
            identity: t.participant.identity
        })));
    }, [tracks]);

    const remoteTrack = tracks.find(t =>
        t.participant.isLocal === false &&
        t.publication.kind === 'video'
    );

    const localTrack = tracks.find(t => t.participant.isLocal === true && t.source === Track.Source.Camera);

    return (
        <div className="w-full h-full relative bg-slate-50 dark:bg-zinc-900">
            {remoteTrack ? (
                <VideoTrack trackRef={remoteTrack} className="w-full h-full object-cover" />
            ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 animate-pulse">
                    <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mb-4">
                        <Bot className="h-8 w-8 text-blue-600" />
                    </div>
                    <span className="text-sm font-medium">Connecting to Avatar...</span>
                </div>
            )}

            {/* PIP Self View */}
            {localTrack && (
                <div className="absolute top-4 right-4 w-28 h-40 bg-black rounded-lg overflow-hidden border border-white/20 shadow-xl z-10 transition-all hover:scale-105">
                    <VideoTrack trackRef={localTrack} className="w-full h-full object-cover mirror" />
                </div>
            )}
        </div>
    );
}

function CustomControls({ onClose }: { onClose: () => void }) {
    const { localParticipant } = useLocalParticipant();
    const [isMuted, setIsMuted] = useState(false);
    const [isVideoOff, setIsVideoOff] = useState(true);

    const toggleMic = async () => {
        if (!localParticipant) return;
        const newState = !isMuted;
        await localParticipant.setMicrophoneEnabled(!newState);
        setIsMuted(newState);
    };

    const toggleCam = async () => {
        if (!localParticipant) return;
        const newState = !isVideoOff;
        await localParticipant.setCameraEnabled(!newState);
        setIsVideoOff(newState);
    };

    useEffect(() => {
        if (localParticipant) {
            setIsMuted(!localParticipant.isMicrophoneEnabled);
            setIsVideoOff(!localParticipant.isCameraEnabled);
        }
    }, [localParticipant]);

    return (
        <>
            <Button
                variant={isMuted ? "destructive" : "secondary"}
                size="icon"
                className="rounded-full h-10 w-10"
                onClick={toggleMic}
            >
                {isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </Button>
            <Button
                variant={isVideoOff ? "destructive" : "secondary"}
                size="icon"
                className="rounded-full h-10 w-10"
                onClick={toggleCam}
            >
                {isVideoOff ? <CameraOff className="h-4 w-4" /> : <Camera className="h-4 w-4" />}
            </Button>
            {/* Upload Button Placeholder */}
            <Button
                variant="outline"
                size="icon"
                className="rounded-full h-10 w-10 bg-slate-100 dark:bg-white/10 border-transparent text-slate-600 dark:text-white hover:bg-slate-200 dark:hover:bg-white/20"
                title="Use Context"
            >
                <Upload className="h-4 w-4" />
            </Button>
            <div className="w-px h-6 bg-slate-200 dark:bg-white/20 mx-1" />
            <Button
                variant="destructive"
                size="icon"
                className="rounded-full h-10 w-10"
                onClick={onClose}
            >
                <Phone className="h-4 w-4 rotate-[135deg]" />
            </Button>
        </>
    );
}

function TranscriptOverlay() {
    const { state } = useVoiceAssistant();
    const [transcript, setTranscript] = useState("");

    return (
        <div className="w-full text-center">
            <AnimatePresence>
                {state === 'speaking' && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="inline-block bg-black/50 backdrop-blur-sm px-4 py-2 rounded-xl text-white text-sm font-medium shadow-sm max-w-[90%]"
                    >
                        Thinking...
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

// --- Helpers ---

function useTokenFetch(mode: string) {
    const [token, setToken] = useState("");
    const [url, setUrl] = useState("");
    const [error, setError] = useState("");
    const [isConnecting, setIsConnecting] = useState(true);
    const [refreshCounter, setRefreshCounter] = useState(0);

    const fetchToken = useCallback(async () => {
        setIsConnecting(true);
        setError("");
        try {
            let sessionId = localStorage.getItem("supa_agent_session_id");
            if (!sessionId) {
                sessionId = `ann_${crypto.randomUUID()}`;
                localStorage.setItem("supa_agent_session_id", sessionId);
            } else if (!sessionId.startsWith("ann_")) {
                sessionId = `ann_${sessionId}`;
                localStorage.setItem("supa_agent_session_id", sessionId);
            }

            const params = new URLSearchParams();
            params.append("mode", mode);
            params.append("session_id", sessionId);

            const resp = await fetch(`/api/agent/voice/token?${params.toString()}`);

            if (!resp.ok) {
                setError("Failed to initialize session");
                return;
            }

            const data = await resp.json();
            if (data.token && data.url) {
                setToken(data.token);
                setUrl(data.url);
            } else {
                setError("Invalid configuration");
            }
        } catch (e) {
            setError("Connection refused");
        } finally {
            setIsConnecting(false);
        }
    }, [mode]);

    useEffect(() => {
        fetchToken();
    }, [fetchToken, refreshCounter]);

    // refresh() triggers a new token fetch without React re-mount
    const refresh = useCallback(() => {
        setToken(""); // Clear old token
        setRefreshCounter(c => c + 1);
    }, []);

    return { token, url, error, isConnecting, refresh };
}

function ErrorDisplay({ error, onClose }: { error: string; onClose: () => void }) {
    return (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 text-center p-6 bg-white dark:bg-zinc-900">
            <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                <X className="h-8 w-8 text-red-500" />
            </div>
            <div className="space-y-2">
                <h3 className="font-semibold text-lg">Unavailable</h3>
                <p className="text-sm text-muted-foreground">{error}</p>
            </div>
            <Button onClick={onClose} variant="outline" size="sm">Go Back</Button>
        </div>
    );
}

function LoadingDisplay() {
    return (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-white dark:bg-zinc-900">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
            <p className="text-sm text-muted-foreground font-medium">Connecting...</p>
        </div>
    );
}

function AgentStatusDisplay() {
    const { state } = useVoiceAssistant();
    const [statusText, setStatusText] = useState("Ready");
    const [statusColor, setStatusColor] = useState("bg-green-500");

    useEffect(() => {
        switch (state) {
            case "connecting":
                setStatusText("Connecting..."); setStatusColor("bg-yellow-500"); break;
            case "listening":
                setStatusText("Listening..."); setStatusColor("bg-green-500"); break;
            case "thinking":
                setStatusText("Thinking..."); setStatusColor("bg-purple-500"); break;
            case "speaking":
                setStatusText("Speaking"); setStatusColor("bg-blue-500"); break;
            default:
                setStatusText("Ready"); setStatusColor("bg-green-500");
        }
    }, [state]);

    return (
        <div className="flex items-center gap-2 mt-6 mb-1">
            <div className={cn("w-2 h-2 rounded-full animate-pulse", statusColor)} />
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{statusText}</span>
        </div>
    );
}

function SimpleVoiceVisualizer() {
    const { state, audioTrack } = useVoiceAssistant();
    return (
        <div className="h-12 flex items-center justify-center gap-1 w-full max-w-[200px]">
            <BarVisualizer state={state} barCount={7} trackRef={audioTrack} className="h-full flex-1" />
        </div>
    );
}
