# Voice Agent Debug Checklist

If you are experiencing issues with the voice agent, please follow these steps:

1.  **Check LiveKit Console:** Ensure `jane-voice-agent` is registered and online.
2.  **Browser Permissions:** Allow microphone access in your browser.
3.  **Check Logs:** View `backend/agent_debug.log` for errors.
4.  **Verify Settings:**
    *   Run `curl http://127.0.0.1:8000/settings` to see the current backend configuration.
    *   Ensure `voice_id` is a valid OpenAI/ElevenLabs voice ID.
    *   Ensure `language` is one of the supported codes (en, es, fr, de, it, pt, zh, ja, ko).

## Common Issues

*   **No Audio:** Check if your system volume is up and the browser tab is not muted.
*   **Wrong Language:** The agent might need a stronger prompt. We've added "IMPORTANT: You must speak in {language}." to the system prompt.
*   **Latency:** We've disabled the heavy `MultilingualModel` turn detector. Latency should now be < 1s.
*   **"Disconnect" Loop:** This was fixed by generating unique room names per session. Refresh the page if this happens.

