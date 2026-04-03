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

    # Patch the session factory to wrap each session's generate_reply
    original_session_factory = realtime_model.session

    def patched_session_factory():
        session = original_session_factory()
        _patch_session_generate_reply(session)
        _patch_session_build_config(session)
        return session

    realtime_model.session = patched_session_factory
    logger.info("✅ Gemini 3.1 patch applied successfully.")
    return True


def _patch_session_generate_reply(session):
    """
    Patches a RealtimeSession's generate_reply to use LiveClientRealtimeInput
    instead of LiveClientContent for text delivery.
    
    The original code (realtime_api.py:702-708) does:
        turns.append(Content(parts=[Part(text=".")], role="user"))
        self._send_client_event(LiveClientContent(turns=turns, turn_complete=True))
    
    Gemini 3.1 rejects this with 1007. Instead we send:
        self._send_client_event(LiveClientRealtimeInput(text=instructions))
        self._send_client_event(LiveClientRealtimeInput(text="."))
    """
    from google.genai import types
    from livekit.agents import llm

    original_generate_reply = session.generate_reply

    def patched_generate_reply(*, instructions=None):
        # Cancel any pending generation (same as original)
        if session._pending_generation_fut and not session._pending_generation_fut.done():
            logger.warning(
                "generate_reply called while another generation is pending, cancelling previous."
            )
            session._pending_generation_fut.cancel("Superseded by new generate_reply call")

        fut = asyncio.Future()
        session._pending_generation_fut = fut

        # End any active user activity (same as original)
        if session._in_user_activity:
            session._send_client_event(
                types.LiveClientRealtimeInput(activity_end=types.ActivityEnd())
            )
            session._in_user_activity = False

        # === THE FIX: Use LiveClientRealtimeInput instead of LiveClientContent ===
        if instructions:
            logger.debug(f"Sending instructions via send_realtime_input (patched): {instructions[:80]}...")
            session._send_client_event(
                types.LiveClientRealtimeInput(text=instructions)
            )

        # Send the trigger text via realtime input (replaces the "." user turn hack)
        session._send_client_event(
            types.LiveClientRealtimeInput(text=".")
        )

        # Timeout handling (same as original)
        def _on_timeout():
            if not fut.done():
                fut.set_exception(
                    llm.RealtimeError(
                        "generate_reply timed out waiting for generation_created event."
                    )
                )
                if session._pending_generation_fut is fut:
                    session._pending_generation_fut = None

        timeout_handle = asyncio.get_event_loop().call_later(8.0, _on_timeout)
        fut.add_done_callback(lambda _: timeout_handle.cancel())

        return fut

    session.generate_reply = patched_generate_reply
    logger.debug("Patched generate_reply on session instance.")


def _patch_session_build_config(session):
    """
    Patches _build_connect_config to add history_config for Gemini 3.1.
    
    Gemini 3.1 requires initial_history_in_client_content=True in the
    history_config for send_client_content to work during initial context seeding.
    """
    from google.genai import types

    def patched_build_config():
        config = original_build_config()
        # We disabled the history_config patch as it was suspected to trigger 1011 errors.
        return config

    session._build_connect_config = patched_build_config
    logger.debug("Patched _build_connect_config on session instance.")
