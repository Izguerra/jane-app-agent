# SupaAgent: Multi-Channel AI Customer Support

SupaAgent is a high-performance, real-time AI customer support platform that enables businesses to deploy intelligent assistants across Web Chat, Voice, AI Avatar, and Meta WhatsApp channels simultaneously.

## ✨ Core Features

- **Multi-Channel Presence:** Unified AI logic for Web Widget, Phone Voice (Inbound/Outbound), Video Avatar, and WhatsApp.
- **Voice Telephony (Telnyx):** Native integration for inbound and outbound calls with SIP bridging to LiveKit agents.
- **Native Multimodal Pipeline:** Direct Audio-to-Audio (A2A) streaming with LiveKit 1.5.1 `AgentSession`, eliminating legacy STT/TTS bottlenecks.
- **Gemini 3.1 Flash Live:** Powered by Google's latest multimodal live model for ultra-low latency conversational AI and native audio reasoning.
- **Intelligent CRM Interaction:** Automatic customer resolution, sales deal tracking, and session management.
- **Heartbeat Mechanism:** Prevents chatbot response stalls during long-running tool executions (e.g., flight searches, web browsing).
- **Proactive Voice & Video Avatar:** High-fidelity real-time interaction powered by LiveKit and Anam/Tavus replicas.

## 🆕 Recent Updates
- **Native Multimodal Migration (v3.0):** Completed transition of Voice and Avatar agents to the native LiveKit 1.5.1 `AgentSession` pipeline. Removed all `DummyTTS` hacks and custom bridges in favor of direct Gemini A2A routing.
- **Chatbot Resiliency:** Implemented a persistent background heartbeat in the `AcknowledgementService` to maintain session responsiveness during heavy tool compute.
- **Avatar Provider Stability:** Standardized Anam as the primary video provider with legacy Tavus support. Improved WebRTC track stabilization with intelligent 1.5s-2.0s post-join delays.
- **E2E Verification Suite:** 100% pass rate on full end-to-end suite (`test_full_e2e.py`) verifying Voice, Avatar, and Tool connectivity across the multimodal pipeline.
- **Gemini 3.1 Support:** Switched to the `v1alpha` API endpoint for `gemini-3.1-flash-live-preview` to support native multimodal modalities (`AUDIO`, `TEXT`).


## 🛠 Tech Stack

- **Frontend:** Next.js, React, Tailwind CSS, shadcn/ui.
- **Backend:** Python (FastAPI), SQLAlchemy, Uvicorn.
- **Telephony:** Telnyx (PSTN), Asterisk (SIP Proxy/Bridge).
- **AI/LLM:** Google Gemini 2.5 Flash Native Audio (Multimodal) — see compatibility note below.
- **Real-time:** LiveKit 1.5.1+ (Voice/Video), Twilio (WhatsApp/SIP).
- **Database:** **PostgreSQL ONLY** (Drizzle on Frontend / SQLAlchemy on Backend) — see critical note below.
- **Payments:** Stripe integration.

> ⚠️ **IMPORTANT: Gemini Model Compatibility**
>
> `gemini-3.1-flash-live-preview` is **currently incompatible** with `livekit-plugins-google==1.5.1`. Using it will cause silent agent failures — the agent connects but never speaks or processes audio.
>
> **Use `gemini-2.5-flash-native-audio-preview` until the upstream fix ships.** See [`docs/GEMINI_MODEL_COMPATIBILITY.md`](docs/GEMINI_MODEL_COMPATIBILITY.md) for full details, upstream issue tracking, and migration instructions.

> ⚠️ **CRITICAL: PostgreSQL is the ONLY supported database**
>
> This application **requires PostgreSQL**. SQLite is NOT supported and MUST NOT be used — not even as a fallback, not for development, not for testing agent connections.
>
> **If PostgreSQL is down or failing, fix PostgreSQL first.** Do not attempt to switch to SQLite or any other database.
>
> The backend's `database/__init__.py` will **raise a hard error** if a SQLite URL is detected or if no PostgreSQL URL is configured. The `.env` file must contain `DATABASE_URL` or `POSTGRES_URL` pointing to a valid PostgreSQL instance.
>
> LiveKit agents run in spawned subprocesses (`multiprocessing.spawn` on macOS). All `.env` loading uses absolute paths derived from `__file__` to ensure the database URL is always resolved correctly in these subprocesses.

## 🚀 Getting Started

### 1. Requirements
Ensure you have Node.js, Python 3.10+, and the Stripe/Twilio/Telnyx configurations ready.

### 2. Development Setup
We use a streamlined development workflow. To start the entire ecosystem (Crawler, Database, Backend, and Frontend):

```bash
/start-dev
```

### 3. Environment Variables
Copy `.env.example` to `.env` and configure your API keys:
- `GOOGLE_GEMINI_API_KEY`
- `LIVEKIT_API_KEY` / `SECRET`
- `TELNYX_API_KEY` / `TELNYX_CONNECTION_ID`
- `STRIPE_SECRET_KEY`
- `POSTGRES_URL`

## 📊 Analytics & Monitoring

SupaAgent provides real-time analytics for all communications.
- **History:** View full transcripts, sentiment analysis, and call outcomes.
- **Analytics:** Monitor message volume, average session duration, and response latency.

## 📅 Roadmap & Future ToDo

### 🤖 Agent Capabilities & Integrations
- [ ] **Agent-Level Authentication**: Migration from Workspace-level to per-Agent tool authentication (Gmail, Calendar, Telnyx).
- [ ] **WhatsApp Integration**: Native Telnyx WhatsApp support with per-agent phone identities.
- [ ] **Outbound Voice**: Proactive agent-initiated calls via LiveKit SIP and Telnyx.
- [ ] **Granular Permissions**: JSONB-based scoping for read/write/delete access on agent tools.
- [ ] **Contact Sync**: Integration with Google People API and Microsoft Graph for unified contact memory.
- [ ] **UX Optimization**: Capability-based cards and integrated "Connect" flows for easier agent configuration.

### 📱 Mobile Companion App
- [ ] **Wake-Word Activation**: Hands-free interaction using `Agent.name` as the wake word (via Porcupine).
- [ ] **Cross-Platform**: Flutter-based iOS/Android app with background listening support.
- [ ] **Device Integration**: Location-aware navigation, camera-based Vision AI, and biometric security (FaceID/TouchID).
- [ ] **Handoff & Sync**: QR-code based workspace synchronization and mobile-to-web memory persistence.

## 📜 Deployment

The application is ready for production deployment on Vercel (Frontend) and any Docker-compatible hosting (Backend). 

Follow the standard Git deployment workflow for updates:
```bash
/git-deployment "feat: describe your change"
```

---
*Built for speed, engagement, and automated customer success.*
