# Jane AI Voice & Chat Agent SaaS

> 24/7 AI-powered voice and text chat agents for healthcare practices using Jane App

---

## 🎯 Project Overview

A HIPAA-compliant SaaS platform that provides Jane App practitioners with AI-powered agents capable of handling:
- 📞 **Voice Calls** - Natural phone conversations for appointment booking
- 💬 **Text Chat** - Website widget for patient inquiries  
- 📅 **Appointment Scheduling** - Seamless Jane App integration
- 💳 **Payment Handling** - Invoice status and payment links
- ❓ **Customer Support** - 24/7 automated responses

**Target Market:** Small to medium healthcare practices (chiropractors, physiotherapists, massage therapists, counselors) using Jane App for practice management.

---

## 📚 Documentation

All project documentation is located in the `/docs` directory:

### Core Documents

| Document | Description | Status |
|----------|-------------|--------|
| [**PRD.md**](./docs/PRD.md) | Product Requirements Document - Features, user stories, success metrics | ✅ Complete |
| [**TECHNICAL_ARCHITECTURE.md**](./docs/TECHNICAL_ARCHITECTURE.md) | System architecture, tech stack, data models, API design | ✅ Complete |
| [**IMPLEMENTATION_PLAN.md**](./docs/IMPLEMENTATION_PLAN.md) | Week-by-week roadmap, milestones, risk management | ✅ Complete |
| [**UI_DESIGN.md**](./docs/UI_DESIGN.md) | Design system, wireframes, component specs, user flows | ✅ Complete |
| [**TODO.md**](./docs/TODO.md) | Comprehensive task list organized by priority and phase | ✅ Complete |

---

## 🏗️ Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────┐
│                   Client Layer                          │
│  Web Dashboard | Chat Widget | Phone Calls (Twilio)    │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              AgentOS (Agno Framework)                    │
│  Multi-tenant agent manager | Session management        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────┬──────────────────┬──────────────────┐
│   Jane App API   │   LiveKit Voice  │   Pinecone RAG   │
│   (Integration)  │   (Pipeline)     │   (Knowledge)    │
└──────────────────┴──────────────────┴──────────────────┘
```

---

## 🛠️ Tech Stack

### Frontend
- **Foundation:** [Next.js SaaS Starter](https://github.com/nextjs/saas-starter)
  - Pre-built authentication (email/password with JWTs)
  - Pre-built Stripe billing integration
  - Pre-built dashboard with CRUD operations
  - Pre-built RBAC (Owner/Member roles)
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS + shadcn/ui
- **Database ORM:** Drizzle ORM (from starter)
- **Deployment:** Vercel (automatic)

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Agent Framework:** Agno 2.0+
- **LLM:** OpenAI GPT-4 Turbo
- **Voice:** LiveKit + Deepgram (STT) + ElevenLabs (TTS)
- **Deployment:** AWS ECS Fargate

### Data
- **Primary DB:** PostgreSQL 15+ (Shared between Next.js and FastAPI)
- **Cache:** Redis 7+
- **Vector DB:** Pinecone
- **Storage:** AWS S3

### Infrastructure
- **Frontend Hosting:** Vercel
- **Backend Hosting:** AWS (ECS, RDS, ElastiCache, S3)
- **CI/CD:** GitHub Actions + Vercel auto-deploy
- **IaC:** Terraform

### Key Integrations
- **Jane App:** OAuth 2.0 + REST API
- **Twilio:** Voice + SMS
- **Stripe:** Billing (pre-configured in SaaS Starter)

**Architecture Decision:** We're using Next.js SaaS Starter as the foundation for our frontend, which provides production-ready authentication, billing, and dashboard components out of the box. This saves 3-5 weeks of development time. The FastAPI backend handles all agent operations and integrations.

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and pnpm
- Python 3.11+
- Docker & Docker Compose
- AWS Account
- Jane App account (for OAuth)
- Stripe account

### Frontend Setup (Next.js SaaS Starter)

```bash
# Clone the SaaS Starter
git clone https://github.com/nextjs/saas-starter jane-voice-agent-frontend
cd jane-voice-agent-frontend

# Install dependencies
pnpm install

# Set up environment variables
cp .env.example .env
# Edit .env with your Stripe keys and database URL

# Run database setup
pnpm db:setup

# Run migrations
pnpm db:migrate

# Seed with test user (test@test.com / admin123)
pnpm db:seed

# Start development server
pnpm dev
```

Visit `http://localhost:3000` and log in with test@test.com / admin123

### Backend Setup (FastAPI Agent Engine)

```bash
# Clone the backend repository
git clone https://github.com/yourorg/jane-voice-agent-backend.git
cd jane-voice-agent-backend

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and database URL (same DB as frontend)

# Run database migrations (for agent tables)
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for API documentation.

### Local Development with Docker Compose

```bash
# Start both services together
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Testing Stripe Integration

Use these test card details:
- Card Number: `4242 4242 4242 4242`
- Expiration: Any future date
- CVC: Any 3-digit number

---

## 📅 Development Timeline

### Phase 1: Foundation (Weeks 1-3)
- Project setup & infrastructure
- Database & authentication
- Jane App OAuth integration

### Phase 2: Text Chat (Weeks 4-6)
- Knowledge base & RAG
- Agno agent implementation
- Embeddable chat widget

### Phase 3: Voice (Weeks 7-9)
- Twilio integration
- LiveKit voice pipeline
- Cross-modal sessions

### Phase 4: Launch (Weeks 10-12)
- Beta testing
- HIPAA compliance review
- Public launch

**Target Launch Date:** 12 weeks from start

---

## 🎯 Key Features

### MVP Features (Week 12)
- ✅ Customer dashboard
- ✅ Jane App integration
- ✅ Knowledge base management
- ✅ Text chat widget
- ✅ Voice call handling
- ✅ Appointment booking (voice + text)
- ✅ Call/chat logging
- ✅ Basic analytics

### Post-MVP (Months 4-6)
- Payment handling
- Sub-agent architecture
- Advanced analytics
- Multi-location support
- White-label options

---

## 🔒 Security & Compliance

### HIPAA Compliance
- ✅ Encryption at rest (AES-256)
- ✅ Encryption in transit (TLS 1.3)
- ✅ Comprehensive audit logging
- ✅ Role-based access control
- ✅ Business Associate Agreements with all vendors
- ✅ Regular security audits

### Required BAAs
- AWS
- Twilio (HIPAA tier)
- OpenAI (Enterprise with BAA)
- Deepgram
- ElevenLabs (verify)
- Pinecone (verify or use pgvector)

---

## 💰 Pricing Strategy

### Subscription Plans

| Plan | Price/Month | Minutes Included | Features |
|------|-------------|------------------|----------|
| **Starter** | $99 | 200 min | Up to 3 practitioners, basic features |
| **Professional** | $199 | 500 min | Up to 10 practitioners, payment handling, sub-agents |
| **Enterprise** | $399 | 1500 min | Unlimited practitioners, white-label, custom integrations |

**Overage:** $0.45-0.50 per additional minute

---

## 📊 Success Metrics

### Primary KPIs
- **Customer Acquisition:** 50 practices in 3 months, 500 by month 12
- **Customer Satisfaction:** >4.5/5 CSAT, >50 NPS
- **Product Performance:** >85% booking success rate, <2s response time
- **Business Growth:** >20% MRR growth, <5% monthly churn

---

## 🤝 Contributing

This is a private repository. For team members:

1. Create feature branch from `develop`
2. Make changes and add tests
3. Create PR with description
4. Get 1 approval
5. Merge to `develop` (auto-deploys to staging)
6. Create release PR to `main` for production

### Code Standards
- **Python:** Black, isort, mypy
- **TypeScript:** ESLint, Prettier
- **Commits:** Conventional Commits format
- **Tests:** >80% coverage required

---

## 📞 Support & Contact

- **Product Owner:** Randy
- **Documentation:** [Internal Wiki TBD]
- **Issues:** GitHub Issues
- **Slack:** #jane-voice-agent

---

## 📝 License

Proprietary - All rights reserved

---

## 🗺️ Project Structure

```
jane-voice-agent-saas/
├── frontend/                    # Next.js SaaS Starter (customized)
│   ├── app/
│   │   ├── (auth)/             # Auth pages (from starter)
│   │   │   ├── sign-in/
│   │   │   └── sign-up/
│   │   ├── (dashboard)/        # Dashboard pages
│   │   │   ├── dashboard/      # Main dashboard (from starter)
│   │   │   ├── settings/       # Settings (from starter)
│   │   │   ├── knowledge-base/ # NEW - KB management
│   │   │   ├── agent-config/   # NEW - Agent settings
│   │   │   ├── calls/          # NEW - Call logs
│   │   │   └── analytics/      # NEW - Analytics
│   │   ├── pricing/            # Pricing page (customized)
│   │   └── api/                # API routes (from starter)
│   ├── components/             # React components
│   ├── lib/
│   │   ├── db/                 # Drizzle schema (from starter)
│   │   ├── auth.ts             # Auth utilities (from starter)
│   │   ├── stripe.ts           # Stripe integration (from starter)
│   │   └── agent-api.ts        # NEW - FastAPI client
│   └── package.json
│
├── backend/                     # FastAPI Agent Engine
│   ├── app/
│   │   ├── agents/             # Agno agent logic
│   │   ├── api/                # API endpoints
│   │   │   ├── agents.py
│   │   │   ├── jane.py
│   │   │   └── voice.py
│   │   ├── db/                 # Database models
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   ├── integrations/       # External APIs
│   │   │   ├── jane.py
│   │   │   ├── twilio.py
│   │   │   └── livekit.py
│   │   ├── services/           # Business logic
│   │   │   ├── knowledge.py
│   │   │   └── voice.py
│   │   └── main.py             # FastAPI app
│   ├── alembic/                # Database migrations
│   ├── tests/
│   └── requirements.txt
│
├── chat-widget/                # Embeddable chat widget
│   └── src/
│
├── infrastructure/             # Terraform/IaC
│   ├── aws/
│   │   ├── rds.tf
│   │   ├── ecs.tf
│   │   └── vpc.tf
│   └── vercel.tf
│
├── docs/                       # Documentation
│   ├── PRD.md
│   ├── TECHNICAL_ARCHITECTURE.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── UI_DESIGN.md
│   ├── TODO.md
│   └── EXECUTIVE_SUMMARY.md
│
├── docker-compose.yml          # Local development
├── .github/
│   └── workflows/             # CI/CD pipelines
│       ├── frontend.yml       # Vercel auto-deploys
│       └── backend.yml        # FastAPI → AWS ECS
└── README.md                  # This file
```

**Key Files:**
- `frontend/lib/agent-api.ts` - API client for FastAPI communication
- `backend/app/agents/` - Agno multi-tenant agent logic
- `backend/app/integrations/jane.py` - Jane App OAuth and API
- `frontend/app/(dashboard)/*/` - Custom dashboard pages

---

## 🎓 Learning Resources

### For New Team Members

**Frameworks & Tools:**
- [Agno Documentation](https://docs.agno.com)
- [LiveKit Agents Guide](https://docs.livekit.io/agents)
- [Next.js App Router](https://nextjs.org/docs/app)
- [FastAPI Tutorial](https://fastapi.tiangolo.com)

**Domain Knowledge:**
- [Jane App API Docs](https://developers.jane.app)
- [HIPAA Compliance Guide](https://www.hhs.gov/hipaa)
- [Twilio Voice Quickstart](https://www.twilio.com/docs/voice)

---

## 🚦 Current Status

**Phase:** Planning & Documentation ✅  
**Next Milestone:** Week 1 - Project Setup  
**Team:** Hiring in progress  
**Funding:** Bootstrapped

---

## 🔮 Vision

Build the #1 AI receptionist platform for healthcare practices, starting with Jane App users and expanding to other practice management systems. Our goal is to help small healthcare businesses provide 24/7 patient support without the overhead of additional staff.

**Long-term Goals:**
- 5,000+ practices using our platform
- Expand to other EMR systems (Cliniko, SimplePractice)
- International markets (Canada, UK, Australia)
- Become the Intercom/Drift of healthcare

---

**Last Updated:** November 22, 2025  
**Version:** 1.0  
**Status:** 📋 Planning Phase
