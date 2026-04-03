import React from 'react';
import { useTrackToggle } from "@livekit/components-react";
import { Track } from "livekit-client";
export default function Test() {
    const { toggle, enabled } = useTrackToggle({ source: Track.Source.Microphone });
    return <button onClick={toggle}>{enabled ? "On" : "Off"}</button>
}
