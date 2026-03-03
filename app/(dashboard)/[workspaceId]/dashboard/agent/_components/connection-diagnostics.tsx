
import { useRoomContext, useRemoteParticipants, useLocalParticipant } from "@livekit/components-react";
import { useEffect, useState } from "react";
import { Copy, Check, Activity } from "lucide-react";

export function ConnectionDiagnostics() {
    const room = useRoomContext();
    const remoteParticipants = useRemoteParticipants();
    const { localParticipant } = useLocalParticipant();
    const [copied, setCopied] = useState(false);

    // Get Tavus Participant (if any)
    const tavusParticipant = remoteParticipants.find(p => p.identity?.includes('tavus') || p.name?.toLowerCase().includes('avatar'));
    const agentParticipant = remoteParticipants.find(p => p.identity?.includes('agent') && !p.identity?.includes('tavus'));

    // Total includes self + remotes
    const totalParticipants = remoteParticipants.length + (localParticipant ? 1 : 0);

    const copyRoom = () => {
        if (room?.name) {
            navigator.clipboard.writeText(room.name);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    if (!room) return null;

    return (
        <div className="absolute top-4 right-4 z-50 pointer-events-auto">
            <div className="bg-black/80 backdrop-blur-md border border-white/10 rounded-lg p-3 text-xs text-white max-w-[220px] shadow-xl">
                <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/10">
                    <Activity className="h-3 w-3 text-green-400" />
                    <span className="font-bold uppercase tracking-wider text-[10px] text-gray-300">Connection Diagnostics</span>
                </div>

                <div className="space-y-1.5">
                    {/* Room Name */}
                    <div className="flex items-center justify-between group cursor-pointer" onClick={copyRoom} title="Click to copy Room Name">
                        <span className="text-gray-400">Room:</span>
                        <div className="flex items-center gap-1">
                            <span className="font-mono text-blue-300 truncate max-w-[100px]">{room.name}</span>
                            {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />}
                        </div>
                    </div>

                    {/* Participant Count */}
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400">Participants:</span>
                        <span className={`font-bold ${totalParticipants >= 3 ? "text-green-400" : "text-yellow-400"}`}>
                            {totalParticipants}/3
                        </span>
                    </div>

                    {/* Tavus Status */}
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400">Avatar:</span>
                        <span className={`${tavusParticipant ? "text-green-400" : "text-red-400"}`}>
                            {tavusParticipant ? "Connected" : "Waiting..."}
                        </span>
                    </div>

                    {/* Agent Status */}
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400">Voice Agent:</span>
                        <span className={`${agentParticipant ? "text-green-400" : "text-red-400"}`}>
                            {agentParticipant ? "Connected" : "Waiting..."}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
