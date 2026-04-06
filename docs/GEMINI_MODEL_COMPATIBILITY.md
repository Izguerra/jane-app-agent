# Gemini Model Compatibility Guide

> **Last Updated:** 2026-04-06
> **LiveKit Version:** `livekit-agents==1.5.1`, `livekit-plugins-google==1.5.1`

This document tracks the compatibility status of Google Gemini Live models with the LiveKit Agents Python SDK. It is critical reading for anyone working on the voice or avatar agent pipelines.

---

## Current Recommended Model

```
gemini-2.5-flash-native-audio-preview
```

This is the stable, tested model for production use with LiveKit 1.5.1.

---

## Model Compatibility Matrix

| Model | Audio-to-Audio (A2A) | `say()` / Greeting | `generate_reply()` | Bidirectional Audio | Tool Calling | Status |
|---|---|---|---|---|---|---|
| `gemini-2.5-flash-native-audio-preview` | ✅ | ✅ | ✅ | ✅ | ✅ | **Recommended** |
| `gemini-2.0-flash-exp` | ✅ | ✅ | ✅ | ✅ | ✅ | Stable fallback |
| `gemini-3.1-flash-live-preview` | ❌ | ❌ | ❌ | ❌ | ⚠️ Untested | **Broken with LiveKit 1.5.1** |

---

## Why Gemini 3.1 Flash Live Is Broken

Gemini 3.1 introduced **breaking API changes** to the Live API that are incompatible with `livekit-plugins-google==1.5.1`:

### 1. `media_chunks` deprecated → must use `audio` field
The LiveKit plugin sends audio via `realtime_input.media_chunks`, but Gemini 3.1 rejects this with:
```
realtime_input.media_chunks is deprecated. Use audio, video, or text instead.
```

### 2. `send_client_content` rejected after first model turn
The plugin uses `send_client_content` for `generate_reply()`, but Gemini 3.1 only allows this for **initial history seeding** (with `history_config.initial_history_in_client_content=true`). After the first model turn, all text input must go through `send_realtime_input`. This causes:
```
Request contains an invalid argument.
```

### 3. Empty `tools`/`sessionResumption` rejected
Stricter validation on 3.1 rejects empty fields that 2.5 silently accepted.

### Symptoms in JaneApp
When running Gemini 3.1:
- Agent connects to the room but **never speaks** (greeting fails silently)
- Agent shows "Listening" state but **never transitions to "Thinking"**
- User audio is received but **never processed** by the model
- Console logs show `ValidationError` on `ChatMessage` construction
- Backend logs show `WebSocket error 1007` or `Request contains an invalid argument`

---

## Upstream References

These are the key upstream issues and PRs tracking the fix:

| Repo | Link | Status |
|---|---|---|
| **Python SDK** (Issue) | [livekit/agents#5234](https://github.com/livekit/agents/issues/5234) | Open |
| **Python SDK** (PR) | [livekit/agents#5251](https://github.com/livekit/agents/pull/5251) | Changes requested — **not merged** |
| **JS SDK** (Issue) | [livekit/agents-js#1179](https://github.com/livekit/agents-js/issues/1179) | Open |
| **JS SDK** (PR) | [livekit/agents-js#1186](https://github.com/livekit/agents-js/pull/1186) | Superseded by #1189 — pending |

### Key Maintainer Feedback

From **davidzhao** (LiveKit CTO) on PR #5251:
> *"I don't think this type of workaround is a good idea. Let's engage the DeepMind folks to understand the best path forward."*
>
> *"This isn't going to work. Realtime input is coming from the end user, but `generate_reply` instructions need to be coming from the model itself."*

From **toubatbrian** (LiveKit maintainer) on PR #1186:
> *"We should hold off on the `generateReply` workaround for Gemini 3.1 until we have a proper upstream direction from the Gemini team."*

**Translation:** The community workaround of routing `generate_reply` through `sendRealtimeInput(text=...)` has a fundamental **semantic mismatch** — the model treats the text as user input, not as an instruction to speak. LiveKit is waiting on official guidance from the Google Gemini team before shipping a fix.

---

## Local Patch Status (`gemini_31_patch.py`)

We maintain a local compatibility patch at `backend/utils/gemini_31_patch.py` that attempts to work around these issues. **This patch is currently non-functional** for the following reasons:

1. It patches `session.generate_reply()` on the raw `RealtimeSession`, but our `MultimodalAgent` bridge calls `AgentSession.say()` which bypasses the patched method entirely.
2. The `audioStreamEnd` helper still uses `media_chunks` (deprecated in 3.1).
3. The fundamental approach is flawed per LiveKit's CTO feedback.

The patch has a **version gate** — it auto-disables for `livekit-plugins-google >= 1.5.2`. When the upstream fix ships, this patch should be removed entirely.

---

## How to Switch Models

The model is configured in `backend/services/voice_pipeline_service.py` → `get_realtime_model()`:

```python
# Primary model (line ~61)
model = google_plugin.realtime.RealtimeModel(
    model="gemini-2.5-flash-native-audio-preview",  # ← Change this
    ...
)
```

### Switching back to 3.1 (when the fix ships)
1. Wait for `livekit-plugins-google >= 1.5.2` release
2. Run `pip install --upgrade livekit-plugins-google`
3. Change the model string to `"gemini-3.1-flash-live-preview"`
4. Remove `backend/utils/gemini_31_patch.py`
5. Run E2E tests: `python -m pytest backend/tests/test_tier1_e2e.py -v`

---

## What Doesn't Change When Switching Models

Both 2.5 and 3.1 use the **same architecture**:
- ✅ Native Audio-to-Audio (A2A) pipeline — no separate STT/TTS
- ✅ Same LiveKit `RealtimeModel` → `AgentSession` flow
- ✅ Same Gemini voices (Puck, Aoede, Charon, etc.)
- ✅ Same function/tool calling support
- ✅ Same frontend code — zero UI changes
- ✅ Same `multimodal_agent.py` bridge — zero backend changes
