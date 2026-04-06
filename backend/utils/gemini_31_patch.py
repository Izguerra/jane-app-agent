"""
Gemini 3.1 Flash Live Compatibility Patch

Addresses the upstream bug in livekit-plugins-google==1.5.1 where
generate_reply() uses send_client_content (LiveClientContent), which
Gemini 3.1 Flash Live rejects with WebSocket error 1007.

This patch intercepts generate_reply() to route text through
send_realtime_input (LiveClientRealtimeInput) instead.

References:
- https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-live-preview
- https://github.com/livekit/agents/pull/5238
- https://github.com/livekit/agents/pull/5251
- https://community.livekit.io/t/gemini-3-1-flash-live/689

TODO: Remove this patch when livekit-plugins-google ships the official fix.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger("gemini-31-patch")

# Models that require send_realtime_input instead of send_client_content
RESTRICTED_CLIENT_CONTENT_MODELS = frozenset({
    "gemini-3.1-flash-live-preview",
    "gemini-3.1-flash-live",
})


def is_restricted_model(model_name: str) -> bool:
    """Check if the model requires the send_realtime_input patch."""
    return model_name in RESTRICTED_CLIENT_CONTENT_MODELS


def patch_realtime_session(realtime_model) -> bool:
    """
    Applies the Gemini 3.1 compatibility patch to a RealtimeModel instance.
    
    This patches the session's generate_reply() method to use
    LiveClientRealtimeInput(text=...) instead of LiveClientContent,
    which Gemini 3.1 rejects after the first model turn.
    
    Returns True if the patch was applied, False if not needed.
    """
    # Version gate: skip if livekit-plugins-google has shipped the official fix
    try:
        import importlib.metadata
        google_plugin_version = importlib.metadata.version("livekit-plugins-google")
        major, minor, patch_v = [int(x) for x in google_plugin_version.split('.')[:3]]
        if (major, minor, patch_v) >= (1, 5, 2):
            logger.info(f"livekit-plugins-google {google_plugin_version} detected — patch likely unnecessary, skipping.")
            return False
    except Exception:
        pass  # Can't determine version, apply patch as safety measure

    try:
        model_name = getattr(realtime_model, '_opts', None)
        if model_name:
            model_name = getattr(model_name, 'model', '')
        else:
            model_name = ''
    except Exception:
        model_name = ''

    if not is_restricted_model(model_name):
        logger.debug(f"Model '{model_name}' does not require Gemini 3.1 patch.")
        return False

    logger.info(f"🔧 Applying Gemini 3.1 compatibility patch for model: {model_name}")
    
    # Verify the session factory is patchable
    if not hasattr(realtime_model, 'session') or not callable(realtime_model.session):
        logger.warning("RealtimeModel does not have a callable 'session' attribute. Cannot apply patch.")
        return False

    # Patch the session factory to wrap each session's generate_reply
    original_session_factory = realtime_model.session

    def patched_session_factory():
        session = original_session_factory()
        
        # Determine model name to pass down for restriction checks
        m_name = getattr(realtime_model, 'model', getattr(realtime_model, '_model', 'Unknown'))
        if not isinstance(m_name, str):
            m_name = 'Unknown'

        _patch_session_generate_reply(session, m_name)
        return session

    realtime_model.session = patched_session_factory
    logger.info("✅ Gemini 3.1 patch applied successfully.")
    return True


def _patch_session_generate_reply(session, model_name: str = "Unknown"):
    # Verify the session has the internal methods we need to patch
    if not hasattr(session, 'generate_reply'):
        logger.warning("Session does not have 'generate_reply' — skipping patch for this session.")
        return
    if not hasattr(session, '_send_client_event'):
        logger.warning("Session does not have '_send_client_event' — skipping patch for this session.")
        return

    from google.genai import types
    from livekit.agents import llm

    async def patched_generate_reply(text: Optional[str] = None, instructions: Optional[str] = None):
        """
        Merged patch for Gemini 3.1 Live.
        Handles both pipeline (text) and native (instructions) signatures.
        Sends a '.' trigger to force generation when text is provided.
        """
        # 1. Normalize input (text or instructions)
        input_text = text or instructions
        
        # 2. Cancel and End Activity (standard logic)
        if hasattr(session, '_pending_generation_fut') and session._pending_generation_fut and not session._pending_generation_fut.done():
            session._pending_generation_fut.cancel("Superseded")
        
        fut = asyncio.Future()
        if hasattr(session, '_pending_generation_fut'): session._pending_generation_fut = fut

        if hasattr(session, '_in_user_activity') and session._in_user_activity:
            session._send_client_event(types.LiveClientRealtimeInput(activity_end=types.ActivityEnd()))
            session._in_user_activity = False

        # 3. Send Text via RealtimeInput (Gemini 3.1 requirement)
        if input_text:
            logger.info(f"⚡ [A2A PUSH] Sending text prompt: {str(input_text)[:100]}...")
            session._send_client_event(types.LiveClientRealtimeInput(text=str(input_text)))
            # The "." trigger is CRITICAL for Gemini 3.1 to start audio generation from text
            logger.info("⚡ [A2A PUSH] Sending '.' trigger for audio generation.")
            session._send_client_event(types.LiveClientRealtimeInput(text="."))
        else:
            logger.debug("No input text for generate_reply - skipping A2A push.")

        # 4. Timeout safety handler (standard)
        def _on_timeout():
            if not fut.done():
                fut.set_exception(llm.RealtimeError("generate_reply timeout"))
                if hasattr(session, '_pending_generation_fut') and session._pending_generation_fut is fut:
                    session._pending_generation_fut = None

        timeout_handle = asyncio.get_event_loop().call_later(12.0, _on_timeout)
        fut.add_done_callback(lambda _: timeout_handle.cancel())

    # Replace the session method
    session.generate_reply = patched_generate_reply

    # 5. Patch _send_task to drop restricted content (PR #5238)
    orig_send_task = session._send_task
    async def patched_send_task(task):
        # If task is LiveClientContent and model is restricted, drop it.
        # This prevents 1007 from tools, system_instruction updates, etc.
        if hasattr(task, 'client_content') and model_name in RESTRICTED_CLIENT_CONTENT_MODELS:
             logger.warning(f"🚫 [A2A GUARD] Dropping restricted client_content for {model_name}")
             return
        return await orig_send_task(task)
    session._send_task = patched_send_task

    logger.info(f"✅ Gemini 3.1 Patch fully applied for {model_name} (PR #5238 Aligned)")

    def send_audio_stream_end():
        logger.debug("Sending audioStreamEnd (Fixes Turn-2 Death)")
        try:
            if not hasattr(session, '_send_client_event'):
                logger.warning("Session missing '_send_client_event' — cannot send audioStreamEnd.")
                return
                
            from google.genai import types as gen_types
            # Use an empty bytes payload instead of None (newer google-genai may reject None)
            session._send_client_event(
                gen_types.LiveClientRealtimeInput(media_chunks=[gen_types.Blob(data=b"", mime_type="audio/pcm")])
            )
        except Exception as e:
            logger.warning(f"audioStreamEnd failed (non-fatal): {e}")
    
    session.send_audio_stream_end = send_audio_stream_end
    logger.debug("Patched generate_reply and initialized tool-call scanner.")
