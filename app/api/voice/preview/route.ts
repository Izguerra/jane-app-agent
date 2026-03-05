
import { NextRequest, NextResponse } from "next/server";
import { OpenAI } from "openai";
import { ElevenLabsClient } from "elevenlabs";

export async function POST(req: NextRequest) {
    try {
        const { provider, voiceId, text } = await req.json();
        const previewText = text || "Hello! Use this to preview my voice.";

        if (!voiceId) {
            return NextResponse.json({ error: "Voice ID is required" }, { status: 400 });
        }

        let audioBuffer: Buffer | null = null;

        if (provider === "openai") {
            const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

            // Map voices that aren't supported by 'tts-1' to distinct valid voices for variety
            const VALID_TTS_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"];

            // Simple deterministic mapping for unsupported voices
            const FALLBACK_MAP: Record<string, string> = {
                "verse": "onyx",
                "ballad": "echo",
                "ash": "fable",
                "coral": "shimmer",
                "sage": "nova"
            };

            let ttsVoice = voiceId;
            if (!VALID_TTS_VOICES.includes(voiceId)) {
                ttsVoice = FALLBACK_MAP[voiceId] || "alloy";
                console.log(`Mapping unsupported TTS voice '${voiceId}' to '${ttsVoice}' for preview.`);
            }

            const response = await openai.audio.speech.create({
                model: "tts-1",
                voice: ttsVoice as any,
                input: previewText,
            });
            const arrayBuffer = await response.arrayBuffer();
            audioBuffer = Buffer.from(arrayBuffer);

        } else if (provider === "elevenlabs") {
            // Handle legacy/mapped ElevenLabs IDs if needed, but assuming frontend sends UUID or valid name
            // Logic for names vs UUIDs: The SDK usually needs UUIDs. 
            // We can use the same mapping logic as the python backend if needed, 
            // but simpler to try and let the frontend send the correct ID (which we fixed?)
            // Actually, frontend has "Rachel", "Adam" (names). ElevenLabs API needs UUIDs.
            // So we MUST Map here too or expose the map. 
            // For speed, let's duplicate the map here or move it to a shared constant.

            const ELEVENLABS_VOICE_MAP: Record<string, string> = {
                "Rachel": "21m00Tcm4TlvDq8ikWAM",
                "Adam": "pNInz6obpgDQGcFmaJgB",
                "Bella": "EXAVITQu4vr4xnSDxMaL",
                "Chris": "iP95p4xoKVk53GoZ742B",
                "Emily": "LcfcDJNUP1GQjkzn1xUU",
                "Josh": "TxGEqnHWrfWFTfGW9XjX",
                "Leo": "IlPhMts77q4KnhTULU2v",
                "Matilda": "XrExE9yKIg1WjnnlVkGX",
                "Nicole": "piTKgcLEGmPE4e6mEKli",
                "Sam": "yoZ06aMxZJJ28mfd3POQ"
            };

            const finalVoiceId = ELEVENLABS_VOICE_MAP[voiceId] || ELEVENLABS_VOICE_MAP[voiceId.charAt(0).toUpperCase() + voiceId.slice(1)] || voiceId;

            // Check API Key
            // Detailed Debugging for 401
            const keyToUse = process.env.ELEVENLABS_API_KEY || process.env.ELEVEN_API_KEY;

            if (!keyToUse) {
                console.error("DEBUG: ElevenLabs Key is MISSING in process.env");
                return NextResponse.json({ error: "ElevenLabs API Key missing in server" }, { status: 500 });
            }

            console.log(`DEBUG: ElevenLabs Key Logic - Key Found. Length: ${keyToUse.length}, Prefix: ${keyToUse.substring(0, 4)}***`);

            const apiKey = keyToUse;

            try {
                // Using raw fetch to debug 401 issues and potential SDK mismatches with new sk_ keys
                const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${finalVoiceId}`, {
                    method: 'POST',
                    headers: {
                        'xi-api-key': apiKey,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: previewText,
                        model_id: "eleven_multilingual_v2",
                        voice_settings: {
                            stability: 0.5,
                            similarity_boost: 0.75
                        }
                    })
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error(`ElevenLabs Raw Fetch Error: Status ${response.status}`, errorText);

                    if (response.status === 401) {
                        // Parse verification
                        return NextResponse.json({ error: `ElevenLabs API Unauthorized (401). Check Permissions (Text-to-Speech) or Key Validity. Trace: ${errorText.substring(0, 100)}` }, { status: 401 });
                    }
                    throw new Error(`ElevenLabs API Error: ${response.status} - ${errorText}`);
                }

                const arrayBuffer = await response.arrayBuffer();
                audioBuffer = Buffer.from(arrayBuffer);

            } catch (error: any) {
                console.error("ElevenLabs Error:", error);
                throw error;
            }

        } else if (provider === "grok") {
            // Grok (xAI) Fallback Preview
            // xAI currently does not have a public REST TTS endpoint for 'preview' in the same way.
            // To satisfy user request for previews, we will map Grok voices to their closest OpenAI equivalents.
            // This is an APPROXIMATION.

            const GROK_MAPPING: Record<string, string> = {
                "ara": "shimmer", // Female
                "eve": "nova",    // Female
                "leo": "echo",    // Male
                "rex": "onyx",    // Male
                "sal": "alloy"    // Male/Neutral
            };

            const mappedVoice = GROK_MAPPING[voiceId.toLowerCase()] || "alloy";
            console.log(`Mapping Grok voice '${voiceId}' to OpenAI '${mappedVoice}' for preview (fallback).`);

            const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
            const response = await openai.audio.speech.create({
                model: "tts-1",
                voice: mappedVoice as any,
                input: previewText,
            });
            const arrayBuffer = await response.arrayBuffer();
            audioBuffer = Buffer.from(arrayBuffer);

        }


        if (!audioBuffer) {
            return NextResponse.json({ error: "Failed to generate audio" }, { status: 500 });
        }

        return new NextResponse(new Uint8Array(audioBuffer), {
            headers: {
                "Content-Type": "audio/mpeg",
                "Content-Length": audioBuffer.length.toString(),
            },
        });

    } catch (error: any) {
        console.error("Preview API Error FULL:", error);
        return NextResponse.json({
            error: error.message,
            stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
        }, { status: 500 });
    }
}
