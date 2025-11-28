# ToDo List
# Jane AI Voice & Chat Agent SaaS

**Version:** 1.0  
**Date:** November 22, 2025  
**Owner:** Randy  
**Status:** Active

---

## How to Use This Document

**Priority Levels:**
- 🔴 **P0 - Critical:** Must have for MVP, blocking
- 🟡 **P1 - High:** Important for MVP, should have
- 🟢 **P2 - Medium:** Nice to have, can defer
- ⚪ **P3 - Low:** Future enhancement

**Status:**
- ☐ **Todo:** Not started
- 🔄 **In Progress:** Currently being worked on
- ✅ **Done:** Completed
- ⏸️ **Blocked:** Waiting on dependency
- ❌ **Cancelled:** No longer needed

---

## Pre-Launch Setup (Week 0)

### Business & Legal
- ☐ 🔴 Register business entity
- ☐ 🔴 Open business bank account
- ☐ 🔴 Purchase domain name (suggest: janeaiagent.com, janevoiceai.com)
- ☐ 🟡 Draft terms of service (with lawyer)
- ☐ 🟡 Draft privacy policy (HIPAA-compliant)
- ☐ 🟡 Get business insurance (E&O, cyber liability)
- ☐ 🟢 Trademark search and filing

### Team & Tools
- ☐ 🔴 Hire/contract engineers (2 full-stack, 1 frontend, 0.5 DevOps)
- ☐ 🔴 Create GitHub organization
- ☐ 🔴 Set up Slack workspace
- ☐ 🟡 Set up Figma team account
- ☐ 🟡 Create project management board (Linear, Jira, or GitHub Projects)
- ☐ 🟢 Set up team email (@yourcompany.com)

### Accounts & Services
- ☐ 🔴 AWS account (production)
- ☐ 🔴 AWS account (staging/dev)
- ☐ 🔴 OpenAI API account
- ☐ 🔴 Pinecone account
- ☐ 🔴 Twilio account (start non-HIPAA, upgrade later)
- ☐ 🔴 Deepgram account
- ☐ 🔴 ElevenLabs account
- ☐ 🔴 Vercel account (for Next.js deployment)
- ☐ 🔴 Stripe account (included in SaaS Starter setup)
- ☐ 🟡 GitHub Actions (included with GitHub)
- ☐ 🟡 Sentry account (error tracking)
- ☐ 🟡 SendGrid account (email)

### SaaS Starter Preparation
- ☐ 🔴 Review Next.js SaaS Starter documentation
- ☐ 🔴 Clone repository and test locally
- ☐ 🔴 Understand authentication flow
- ☐ 🔴 Review Stripe integration
- ☐ 🔴 Review database schema (Drizzle ORM)
- ☐ 🔴 Plan customizations needed

---

## Phase 1: Foundation (Weeks 1-3)

### Week 1: SaaS Starter Setup & FastAPI Init

#### 🔴 P0 - Next.js SaaS Starter Setup
- ☐ Clone Next.js SaaS Starter repository
- ☐ Install dependencies (`pnpm install`)
- ☐ Run database setup (`pnpm db:setup`)
- ☐ Run migrations (`pnpm db:migrate`)
- ☐ Seed database with test user (`pnpm db:seed`)
- ☐ Test authentication (login with test@test.com)
- ☐ Test Stripe checkout flow (use test card)
- ☐ Review existing codebase structure
- ☐ Understand Drizzle ORM setup

#### 🔴 P0 - Customization
- ☐ Update branding (logo, company name)
- ☐ Modify landing page copy
- ☐ Update pricing page to $99/$199/$399 tiers
- ☐ Configure Stripe products for new pricing
- ☐ Customize email templates
- ☐ Update terms of service
- ☐ Update privacy policy

#### 🔴 P0 - Add New Pages (Placeholders)
- ☐ Create `/app/(dashboard)/knowledge-base` route
- ☐ Create `/app/(dashboard)/agent-config` route
- ☐ Create `/app/(dashboard)/calls` route
- ☐ Create `/app/(dashboard)/analytics` route
- ☐ Add navigation items to sidebar
- ☐ Create basic layout for each page

#### 🔴 P0 - Database Extensions
- ☐ Add migration for `customers` table (links to SaaS Starter teams)
- ☐ Add migration for `agent_configs` table
- ☐ Add migration for `practitioners` table
- ☐ Add migration for `knowledge_docs` table
- ☐ Test migrations don't conflict with SaaS Starter tables
- ☐ Verify user signup still works

#### 🔴 P0 - FastAPI Backend Setup
- ☐ Create new repository: `jane-voice-agent-backend`
- ☐ FastAPI boilerplate project structure
- ☐ Basic FastAPI app with health check
- ☐ Configure CORS for Next.js frontend
- ☐ Connect to shared PostgreSQL database
- ☐ Create SQLAlchemy models for custom tables
- ☐ Docker Compose for local development
- ☐ Test connection between Next.js and FastAPI

#### 🔴 P0 - API Client Layer
- ☐ Create `/lib/agent-api.ts` in Next.js
- ☐ Add environment variable for FastAPI URL
- ☐ Create TypeScript types for API responses
- ☐ Add error handling utilities
- ☐ Add loading state management
- ☐ Test basic API call to FastAPI

#### 🔴 P0 - AWS Infrastructure
- ☐ Create VPC with subnets
- ☐ Provision RDS PostgreSQL (shared for both services)
- ☐ Set up ElastiCache Redis
- ☐ Create S3 buckets
- ☐ Configure Secrets Manager
- ☐ Set up IAM roles

#### 🟡 P1 - CI/CD Setup
- ☐ Connect Next.js repo to Vercel
- ☐ Configure Vercel environment variables
- ☐ Test automatic Vercel deployments
- ☐ GitHub Actions for FastAPI tests
- ☐ GitHub Actions for Docker build
- ☐ Push Docker images to ECR
- ☐ Deploy FastAPI to ECS staging

#### 🟢 P2 - Documentation
- ☐ Update README with new setup instructions
- ☐ Document local development workflow
- ☐ Document deployment process
- ☐ Create architecture diagram

---

### Week 2: Database & Authentication

#### 🔴 P0 - Database Schema
- ☐ Design final schema (review with team)
- ☐ Set up Alembic for migrations
- ☐ Create initial migration script
- ☐ SQLAlchemy models:
  - ☐ Customer model
  - ☐ AgentConfig model
  - ☐ Practitioner model
  - ☐ Session model
  - ☐ Message model
  - ☐ CallLog model
  - ☐ KnowledgeDoc model
- ☐ Database seeding scripts for testing
- ☐ Test migration up/down

#### 🔴 P0 - Authentication System
- ☐ JWT token generation logic
- ☐ Password hashing with bcrypt
- ☐ User registration endpoint (`POST /auth/signup`)
- ☐ Login endpoint (`POST /auth/login`)
- ☐ Refresh token endpoint (`POST /auth/refresh`)
- ☐ Get current user endpoint (`GET /auth/me`)
- ☐ Auth middleware for protected routes
- ☐ Rate limiting with Redis
- ☐ Unit tests for auth logic

#### 🔴 P0 - Frontend Dashboard
- ☐ Main dashboard layout
- ☐ Navigation sidebar component
- ☐ User profile page
- ☐ Settings page structure
- ☐ Loading states (spinners, skeletons)
- ☐ Error boundary component

#### 🟡 P1 - Forms & Validation
- ☐ React Hook Form setup
- ☐ Zod validation schemas
- ☐ Reusable form components
  - ☐ Input field
  - ☐ Select dropdown
  - ☐ Textarea
  - ☐ Checkbox
  - ☐ Radio group
- ☐ Error display components
- ☐ Form submission loading states

#### 🟢 P2 - Testing
- ☐ Unit tests for auth endpoints
- ☐ Integration tests for database operations
- ☐ Frontend component tests (React Testing Library)

---

### Week 3: Jane App Integration

#### 🔴 P0 - Jane OAuth Flow
- ☐ Register OAuth app with Jane App
- ☐ OAuth authorization URL generation
- ☐ OAuth callback endpoint (`GET /auth/jane/callback`)
- ☐ Token exchange logic
- ☐ Store encrypted tokens in database (use Fernet)
- ☐ Token refresh mechanism
- ☐ Handle OAuth errors gracefully

#### 🔴 P0 - Jane API Client
- ☐ Create `JaneAPIClient` class
- ☐ Implement endpoints:
  - ☐ Get practitioners (`/practitioners`)
  - ☐ Get services (`/services`)
  - ☐ Get availability (`/appointments/availability`)
  - ☐ Create appointment (`POST /appointments`)
  - ☐ Find patient (`/patients/search`)
  - ☐ Create patient (`POST /patients`)
  - ☐ Get invoice (`/invoices/{id}`)
- ☐ Error handling and retries (exponential backoff)
- ☐ Rate limiting logic (token bucket)
- ☐ Response caching with Redis
- ☐ Unit tests with mocked responses

#### 🔴 P0 - Frontend Jane Connection
- ☐ "Connect Jane" button/page
- ☐ OAuth redirect handling
- ☐ Connection status display
- ☐ Sync status indicator (last synced time)
- ☐ Disconnect Jane option
- ☐ Error handling for failed connections

#### 🟡 P1 - Jane Data Display
- ☐ Practitioners list view
- ☐ Services list view
- ☐ Last sync timestamp
- ☐ Manual sync trigger button
- ☐ Loading states during sync

#### 🟢 P2 - Testing
- ☐ End-to-end OAuth flow test
- ☐ Test with Jane sandbox environment
- ☐ Mock Jane API for CI/CD tests

---

## Phase 2: Text Chat Agent (Weeks 4-6)

### Week 4: Knowledge Base & RAG

#### 🔴 P0 - Pinecone Integration
- ☐ Create Pinecone account and API key
- ☐ Initialize Pinecone index (dimension: 1536)
- ☐ Implement namespace per customer
- ☐ OpenAI embeddings integration
- ☐ Vector upsert logic
- ☐ Vector search logic

#### 🔴 P0 - Knowledge Base Service
- ☐ Create `KnowledgeBaseService` class
- ☐ Add document method
- ☐ Search method (RAG)
- ☐ Sync from Jane (auto-populate practitioners/services)
- ☐ Document upload endpoint (`POST /knowledge/documents`)
- ☐ Text extraction from PDF (PyPDF2)
- ☐ Text extraction from Word (python-docx)
- ☐ Intelligent chunking (500 tokens, 50 overlap)
- ☐ Metadata management

#### 🔴 P0 - Frontend Knowledge Base UI
- ☐ Knowledge base management page
- ☐ Auto-sync status display
- ☐ Manual document upload component
- ☐ File upload progress indicator
- ☐ FAQ builder component
- ☐ Practice info form

#### 🟡 P1 - Document Management
- ☐ Document list view
- ☐ Preview documents (modal)
- ☐ Edit document metadata
- ☐ Delete documents (with confirmation)
- ☐ Search knowledge base (test RAG)

#### 🟢 P2 - Testing
- ☐ Upload various document types (PDF, Word, TXT)
- ☐ Test RAG search accuracy
- ☐ Benchmark embedding speed
- ☐ Test chunking logic

---

### Week 5: Agno Agent Implementation

#### 🔴 P0 - Agno Framework Setup
- ☐ Install Agno (`pip install agno`)
- ☐ AgentOS boilerplate setup
- ☐ Basic agent configuration
- ☐ PostgreSQL connection for Agno sessions

#### 🔴 P0 - Agent Development
- ☐ Create `MultiTenantAgentManager` class
- ☐ Agent initialization logic per customer
- ☐ System prompt templates
- ☐ Implement tool functions:
  - ☐ `check_availability(date, practitioner_id)`
  - ☐ `book_appointment(datetime, service_id, patient_name, patient_phone)`
  - ☐ `answer_question(query)` - uses RAG
  - ☐ `get_invoice_status(invoice_id)`
- ☐ Session management
- ☐ Agent testing endpoint (`POST /agents/test`)

#### 🔴 P0 - Frontend Agent Configuration
- ☐ Agent settings page
- ☐ System prompt editor (textarea)
- ☐ Voice settings selector (TTS voice, speed)
- ☐ Business hours configuration
- ☐ Enabled features toggles
- ☐ Save settings button

#### 🟡 P1 - Agent Testing Playground
- ☐ Chat interface for testing agent
- ☐ Display tool calls in debug panel
- ☐ Show knowledge base hits
- ☐ Response time display
- ☐ Clear conversation button

#### 🟢 P2 - Testing
- ☐ Test agent with various booking intents
- ☐ Verify tool execution
- ☐ Check RAG integration accuracy
- ☐ Load test agent initialization (<3s)

---

### Week 6: Chat Widget

#### 🔴 P0 - Chat Widget Development
- ☐ Standalone React chat component
- ☐ WebSocket connection logic
- ☐ Message list with auto-scroll
- ☐ Input field with send button
- ☐ Typing indicators
- ☐ Message bubble components (user/agent)
- ☐ Timestamps

#### 🔴 P0 - Widget Integration
- ☐ Web Component wrapper
- ☐ Build script for standalone bundle
- ☐ CDN hosting (S3 + CloudFront)
- ☐ Embed code generator
- ☐ Installation instructions
- ☐ Customization options (colors, position)
- ☐ Mobile responsive design

#### 🔴 P0 - Backend WebSocket
- ☐ WebSocket endpoint (`/ws/chat/{session_id}`)
- ☐ Connection management
- ☐ Message broadcasting
- ☐ Session association
- ☐ Error handling

#### 🟡 P1 - Chat API Endpoints
- ☐ Create session (`POST /chat/sessions`)
- ☐ Send message (`POST /chat/sessions/{id}/messages`)
- ☐ Get history (`GET /chat/sessions/{id}`)
- ☐ End session (`DELETE /chat/sessions/{id}`)
- ☐ Session analytics logging

#### 🟢 P2 - Enhanced Features
- ☐ Quick reply buttons
- ☐ Date picker integration
- ☐ Time slot selector
- ☐ Booking confirmation card

#### 🟢 P2 - Testing
- ☐ End-to-end booking via chat
- ☐ Multiple concurrent sessions
- ☐ Widget on different websites
- ☐ Mobile browser testing (iOS Safari, Android Chrome)

---

## Phase 3: Voice Integration (Weeks 7-9)

### Week 7: Twilio & Phone Setup

#### 🔴 P0 - Twilio Integration
- ☐ Create Twilio account
- ☐ Upgrade to HIPAA-compliant tier
- ☐ Sign Business Associate Agreement (BAA)
- ☐ Install Twilio SDK (`pip install twilio`)
- ☐ Number provisioning logic
- ☐ Webhook handler for incoming calls (`POST /voice/incoming/{customer_id}`)
- ☐ Call routing logic (identify customer by number)

#### 🔴 P0 - Call Management
- ☐ Call logging to database
- ☐ SMS sending for confirmations
- ☐ Call status tracking (webhook: `/voice/status/{customer_id}`)
- ☐ Recording management (optional, with consent)
- ☐ Call transcript storage

#### 🔴 P0 - Frontend Phone Management
- ☐ Display assigned phone number
- ☐ Setup instructions page (how to forward calls)
- ☐ Test call button (initiate test)
- ☐ Call forwarding guide (step-by-step)

#### 🟡 P1 - Call Logs UI
- ☐ Call history list
- ☐ Call details view (modal)
- ☐ Transcript display
- ☐ Filtering (date, outcome)
- ☐ Search functionality
- ☐ Export to CSV

#### 🟢 P2 - Testing
- ☐ Test inbound call routing
- ☐ Verify customer lookup by phone
- ☐ Test SMS sending
- ☐ Check call logging accuracy

---

### Week 8: LiveKit Voice Pipeline

#### 🔴 P0 - LiveKit Setup
- ☐ Choose: LiveKit Cloud vs. self-hosted
- ☐ Deploy LiveKit server (if self-hosted)
- ☐ Configure SIP trunking
- ☐ Generate access tokens
- ☐ Test basic voice connection

#### 🔴 P0 - Voice Agent Integration
- ☐ Install LiveKit Agents SDK
- ☐ Create `VoicePipelineAdapter` class
- ☐ Bridge Agno agent to LiveKit
- ☐ Configure voice pipeline:
  - ☐ STT (Deepgram Nova-2)
  - ☐ LLM (Agno wrapper)
  - ☐ TTS (ElevenLabs)
  - ☐ VAD (Silero)
- ☐ Connect Twilio → LiveKit
- ☐ Voice-specific prompts (shorter responses)
- ☐ Interrupt handling

#### 🔴 P0 - Testing
- ☐ End-to-end voice call test
- ☐ Measure latency (<500ms target)
- ☐ Test speech recognition accuracy
- ☐ Assess voice quality
- ☐ Test with background noise
- ☐ Test interrupt handling

#### 🟡 P1 - Voice Optimization
- ☐ Reduce latency (caching, connection pooling)
- ☐ Tune STT settings
- ☐ Optimize TTS speed vs. quality
- ☐ Test different voice options

---

### Week 9: Cross-Modal Sessions & Polish

#### 🔴 P0 - Session Continuity
- ☐ Unified session model (text + voice)
- ☐ Link chat and voice sessions
- ☐ Context preservation logic
- ☐ Handoff mechanism (chat → voice)
- ☐ Session lookup by phone number

#### 🔴 P0 - Frontend Cross-Modal UI
- ☐ "Call Me" button in chat widget
- ☐ Phone number input for callback
- ☐ Session continuity indicator
- ☐ Voice call initiation flow

#### 🟡 P1 - Analytics Dashboard
- ☐ Usage overview cards (calls, chats, bookings, minutes)
- ☐ Call/chat volume chart (line chart)
- ☐ Booking success rate
- ☐ Cost tracking display
- ☐ Top questions list
- ☐ Peak hours chart

#### 🔴 P0 - Performance Optimization
- ☐ Voice latency reduction
- ☐ Agent response speed tuning
- ☐ Database query optimization
- ☐ Add database indexes
- ☐ Redis caching optimization
- ☐ Error handling improvements

#### 🟢 P2 - Testing
- ☐ Test chat → voice handoff
- ☐ Load testing (100+ concurrent users)
- ☐ Stress testing (peak loads)
- ☐ Security penetration test

---

## Phase 4: Launch Preparation (Weeks 10-12)

### Week 10: Beta Testing & Bug Fixes

#### 🔴 P0 - Beta Program
- ☐ Identify 10 beta candidates (Jane App users)
- ☐ Create beta landing page
- ☐ Onboarding guide for beta testers
- ☐ Feedback collection form (Typeform or Google Forms)
- ☐ Beta sign-up form

#### 🔴 P0 - Beta Support
- ☐ Onboard first 3 beta customers
- ☐ Daily check-ins with beta users (Slack or email)
- ☐ Bug triage and prioritization
- ☐ Hot fixes deployed as needed
- ☐ Document common issues (FAQ for support)

#### 🟡 P1 - Documentation
- ☐ User guide (getting started)
- ☐ Knowledge base setup guide
- ☐ FAQ for customers
- ☐ Troubleshooting guide
- ☐ Video walkthrough (Loom)

#### 🟢 P2 - Internal
- ☐ API documentation (if exposing)
- ☐ Architecture decision records
- ☐ Runbook for operations

---

### Week 11: Polish & Compliance

#### 🔴 P0 - HIPAA Compliance
- ☐ Security risk assessment
- ☐ Review all BAAs:
  - ☐ Twilio BAA signed
  - ☐ OpenAI BAA signed
  - ☐ AWS BAA signed
  - ☐ Deepgram BAA signed
  - ☐ ElevenLabs BAA (check availability)
  - ☐ Pinecone BAA (check availability)
- ☐ Audit logging verification
- ☐ Encryption validation (at rest, in transit)
- ☐ Access control review (RBAC)
- ☐ Incident response plan documented
- ☐ Breach notification procedures
- ☐ Employee HIPAA training materials

#### 🟡 P1 - Legal Documents
- ☐ Finalize privacy policy
- ☐ Finalize terms of service
- ☐ Cookie policy
- ☐ Data processing agreement (DPA)
- ☐ Legal review of all documents

#### 🔴 P0 - UI/UX Polish
- ☐ UI consistency pass
- ☐ Error messages user-friendly
- ☐ Loading states polished
- ☐ Mobile optimization
- ☐ Accessibility improvements (WCAG 2.1 AA)
- ☐ Onboarding flow refinement

#### 🔴 P0 - Performance
- ☐ Load testing results analysis
- ☐ Performance bottlenecks addressed
- ☐ Caching strategy refined
- ☐ Database indexes optimized
- ☐ Image optimization
- ☐ Code splitting for frontend

#### 🟢 P2 - Nice to Have
- ☐ Dark mode support
- ☐ Animations and micro-interactions
- ☐ Custom illustrations

---

### Week 12: Launch Preparation

#### 🔴 P0 - Production Infrastructure
- ☐ Scale production environment (multi-AZ)
- ☐ Set up monitoring dashboards (CloudWatch)
- ☐ Configure alerting rules (PagerDuty/Slack)
- ☐ Backup verification (test restore)
- ☐ Disaster recovery test
- ☐ Status page setup (e.g., Statuspage.io)

#### 🔴 P0 - Marketing Site
- ☐ Landing page design
- ☐ Product demo video (3-5 minutes)
- ☐ Pricing page
- ☐ Sign-up flow
- ☐ Email capture (mailing list)
- ☐ Analytics tracking (Plausible or Fathom)
- ☐ SEO optimization (meta tags, sitemap)

#### 🟡 P1 - Launch Activities
- ☐ Soft launch announcement (email to beta users)
- ☐ Product Hunt submission
- ☐ Post in Jane App user groups (Facebook, Reddit)
- ☐ Direct outreach to 50 prospects
- ☐ Blog post about launch
- ☐ PR outreach (healthcare tech press)
- ☐ Social media posts (LinkedIn, Twitter)

#### 🔴 P0 - Support Readiness
- ☐ Support email setup (support@yourcompany.com)
- ☐ Help documentation live
- ☐ Customer onboarding checklist
- ☐ Billing system tested (Stripe)
- ☐ Refund policy established
- ☐ Escalation procedures

#### 🟡 P1 - Billing Setup
- ☐ Stripe integration
- ☐ Subscription plans configured
- ☐ Usage tracking (minutes, calls)
- ☐ Invoice generation
- ☐ Payment method management
- ☐ Upgrade/downgrade flows

---

## Post-Launch (Months 4-6)

### Month 4: Stabilization

#### 🔴 P0 - Monitoring & Fixes
- ☐ Monitor production performance daily
- ☐ Fix critical bugs (P0 within 24h)
- ☐ Address customer feedback
- ☐ Improve onboarding based on data

#### 🟡 P1 - Optimization
- ☐ Cost optimization (reserved instances, spot)
- ☐ Performance improvements
- ☐ Reduce churn (analyze cancellations)

---

### Month 5: Payment Features

#### 🟡 P1 - Payment Handling
- ☐ Add payment tools to agent
- ☐ Invoice status checking from Jane
- ☐ Payment link generation
- ☐ Stripe integration for payments
- ☐ Payment confirmation flow

---

### Month 6: Advanced Features

#### 🟡 P1 - Sub-Agent Architecture
- ☐ Sub-agent per practitioner
- ☐ Practitioner-specific prompts
- ☐ Routing logic
- ☐ Handoff mechanism

#### 🟡 P1 - Advanced Analytics
- ☐ Advanced dashboard
- ☐ Export reports (CSV, PDF)
- ☐ Customer insights

#### 🟢 P2 - Email/SMS Automation
- ☐ Appointment reminders
- ☐ Follow-up messages
- ☐ Re-engagement campaigns

---

## Ongoing / Maintenance

### Infrastructure
- ☐ Weekly: Review CloudWatch metrics
- ☐ Weekly: Check error rates in Sentry
- ☐ Monthly: Review AWS costs
- ☐ Monthly: Security updates
- ☐ Quarterly: Disaster recovery drill
- ☐ Quarterly: Penetration testing

### Product
- ☐ Weekly: Customer feedback review
- ☐ Weekly: Bug triage
- ☐ Bi-weekly: Sprint planning
- ☐ Monthly: Product roadmap review
- ☐ Quarterly: User research

### Compliance
- ☐ Quarterly: HIPAA security review
- ☐ Annually: Formal security audit
- ☐ Annually: HIPAA risk assessment
- ☐ Ongoing: Employee training

---

## Backlog / Future Ideas

### Features
- ☐ 🟢 Multi-location support
- ☐ 🟢 Insurance verification
- ☐ 🟢 Waitlist management
- ☐ 🟢 Video consultations
- ☐ 🟢 Patient portal integration
- ☐ 🟢 Email agent (in addition to voice/chat)
- ☐ 🟢 WhatsApp integration
- ☐ 🟢 Appointment reminders (automated)
- ☐ 🟢 Review request automation
- ☐ 🟢 White-label options
- ☐ 🟢 API for third-party integrations
- ☐ 🟢 Mobile app (iOS/Android)

### Integrations
- ☐ 🟢 Google Calendar sync
- ☐ 🟢 Zapier integration
- ☐ 🟢 Other EMR systems (Cliniko, SimplePractice)
- ☐ 🟢 Slack notifications for practices
- ☐ 🟢 CRM integrations (Salesforce, HubSpot)

### Technical Improvements
- ☐ 🟢 GraphQL API (in addition to REST)
- ☐ 🟢 Real-time dashboard (WebSocket updates)
- ☐ 🟢 Voice cloning for personalized agents
- ☐ 🟢 Sentiment analysis on calls
- ☐ 🟢 Agent performance A/B testing
- ☐ 🟢 Multi-language support

---

## Dependencies & Blockers

### External Dependencies
- ⏸️ Jane App OAuth approval (waiting on Jane)
- ⏸️ Twilio HIPAA tier approval (1-2 weeks)
- ⏸️ LiveKit BAA availability (need to verify)

### Internal Dependencies
- ⏸️ Hiring: Need engineers before Week 1
- ⏸️ Design: Need UI mockups before Week 4
- ⏸️ Legal: Need ToS/Privacy Policy before Week 11

### Critical Path
- 🔴 Jane integration must complete before Knowledge Base (Week 3 → Week 4)
- 🔴 Text chat must work before Voice (Week 6 → Week 8)
- 🔴 Beta testing must complete before Launch (Week 10 → Week 12)

---

## Notes & Decisions

### Architecture Decisions
- ✅ Using Agno for multi-modal agents (voice + text)
- ✅ Pinecone for vector DB (can switch to pgvector later)
- ✅ AWS for hosting (HIPAA-compliant setup)
- ✅ FastAPI for backend (async-native)
- ✅ Next.js for frontend (SSR, good DX)

### Open Questions
- ❓ LiveKit HIPAA compliance - verify or self-host?
- ❓ Pinecone cost at scale - evaluate pgvector alternative?
- ❓ Jane API rate limits - get official documentation
- ❓ Voice quality benchmarks - what's acceptable latency?

### Risks
- ⚠️ Jane App integration complexity
- ⚠️ Voice quality/latency issues
- ⚠️ HIPAA compliance gaps
- ⚠️ Beta customer acquisition
- ⚠️ Team availability/bandwidth

---

## Quick Reference

### Key Milestones
- 📅 Week 3: Jane integration working
- 📅 Week 6: Text chat operational
- 📅 Week 9: Voice calls working
- 📅 Week 12: Public beta launch

### Critical Contacts
- Jane App Support: support@jane.app
- AWS Support: via console
- Twilio Support: help.twilio.com
- Legal Counsel: [TBD]

### Important Links
- GitHub Repo: [TBD]
- Staging Environment: [TBD]
- Production: [TBD]
- Documentation: [TBD]
- Figma Designs: [TBD]

---

**Last Updated:** November 22, 2025  
**Next Review:** Weekly during development  
**Owner:** Randy
