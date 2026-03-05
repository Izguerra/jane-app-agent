# SupaAgent: Multi-Channel AI Customer Support

SupaAgent is a high-performance, real-time AI customer support platform that enables businesses to deploy intelligent assistants across Web Chat, Voice, AI Avatar, and Meta WhatsApp channels simultaneously.

## ✨ Core Features

- **Multi-Channel Presence:** Unified AI logic for Web Widget, Phone Voice, Video Avatar, and WhatsApp.
- **Real-Time Streaming:** Near-zero latency interaction using FastAPI StreamingResponse and TextDecoder browser streaming.
- **Gemini 3.0 Flash Integration:** Powered by Google's latest `gemini-3-flash-preview` for industry-leading response times and TTFT (Time-to-First-Token).
- **Intelligent CRM Interaction:** Automatic customer resolution, sales deal tracking, and session management.
- **Auto-Closure Logic:** Automated background scheduler that cleans up idle sessions after 2 minutes of inactivity.
- **Voice & Video Avatar:** High-fidelity spoken interaction powered by LiveKit and Tavus replicas.
- **Marketing & Dashboard:** Built-in landing page, pricing with Stripe, and comprehensive analytics for tracking communication history and outcomes.

## 🛠 Tech Stack

- **Frontend:** Next.js, React, Tailwind CSS, shadcn/ui.
- **Backend:** Python (FastAPI), SQLAlchemy, Uvicorn.
- **AI/LLM:** Google Gemini 3.0 Flash.
- **Real-time:** LiveKit (Voice/Video), Twilio (WhatsApp/SIP).
- **Database:** Postgres (Drizzle on Frontend / SQLAlchmey on Backend).
- **Payments:** Stripe integration.

## 🚀 Getting Started

### 1. Requirements
Ensure you have Node.js, Python 3.10+, and the Stripe/Twilio CLIs installed.

### 2. Development Setup
We use a streamlined development workflow. To start the entire ecosystem (Crawler, Database, Backend, and Frontend):

```bash
/start-dev
```

### 3. Environment Variables
Copy `.env.example` to `.env` and configure your API keys:
- `GOOGLE_GEMINI_API_KEY`
- `LIVEKIT_API_KEY` / `SECRET`
- `STRIPE_SECRET_KEY`
- `POSTGRES_URL`

## 📊 Analytics & Monitoring

SupaAgent provides real-time analytics for all communications.
- **History:** View full transcripts, sentiment analysis, and call outcomes.
- **Analytics:** Monitor message volume, average session duration, and response latency.

## 📜 Deployment

The application is ready for production deployment on Vercel (Frontend) and any Docker-compatible hosting (Backend). 

Follow the standard Git deployment workflow for updates:
```bash
/git-deployment "feat: describe your change"
```

---
*Built for speed, engagement, and automated customer success.*
