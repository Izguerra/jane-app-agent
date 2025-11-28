# Implementation Plan
# Jane AI Voice & Chat Agent SaaS

**Version:** 1.0  
**Date:** November 22, 2025  
**Timeline:** 12 weeks to MVP  
**Team:** To be staffed

---

## Executive Summary

This implementation plan outlines a 12-week roadmap to build and launch the MVP of our Jane AI Voice & Chat Agent SaaS platform. The plan is divided into 4 phases:

1. **Foundation** (Weeks 1-3): Infrastructure, auth, Jane integration
2. **Text Chat** (Weeks 4-6): Chat widget, knowledge base, Agno agents
3. **Voice Integration** (Weeks 7-9): Voice pipeline, Twilio, cross-modal sessions
4. **Launch Prep** (Weeks 10-12): Beta testing, polish, go-to-market

**Key Milestones:**
- Week 3: Jane integration working
- Week 6: Text chat agent operational
- Week 9: Voice calls working end-to-end
- Week 12: Public beta launch

---

## Team Requirements

### Minimum Viable Team

**Full-Stack Engineer (2x):**
- Primary focus: Backend (FastAPI, Agno, Jane integration)
- Secondary: Frontend (Next.js dashboard)

**Frontend Engineer (1x):**
- Dashboard and chat widget
- React, TypeScript

**DevOps Engineer (0.5x - part-time or contractor):**
- AWS setup, CI/CD
- Docker, Terraform

**Product Manager (Randy):**
- Requirements, testing, customer feedback

**Optional:**
- UI/UX Designer (contractor for first 2 weeks)
- QA Engineer (can be covered by engineers initially)

---

## Phase 1: Foundation (Weeks 1-3)

### Week 1: Project Setup & SaaS Starter Customization

**Goals:**
- Next.js SaaS Starter cloned and customized
- FastAPI backend repository initialized
- Shared database configured
- CI/CD pipelines working

#### Frontend Tasks (Next.js SaaS Starter)

**Day 1: Clone and Setup**
- [ ] Clone Next.js SaaS Starter
  ```bash
  git clone https://github.com/nextjs/saas-starter jane-voice-agent-frontend
  cd jane-voice-agent-frontend
  pnpm install
  ```
- [ ] Run database setup script
  ```bash
  pnpm db:setup
  pnpm db:migrate
  pnpm db:seed
  ```
- [ ] Test authentication flow (login with test@test.com)
- [ ] Test Stripe integration (use test card)
- [ ] Review existing codebase structure

**Day 2: Branding Customization**
- [ ] Update logo and company name
- [ ] Modify landing page copy
- [ ] Update pricing page ($99/$199/$399 tiers)
- [ ] Customize email templates
- [ ] Update terms of service template
- [ ] Update privacy policy template

**Day 3: Add New Pages (Placeholders)**
- [ ] Create `/app/(dashboard)/knowledge-base` page
- [ ] Create `/app/(dashboard)/agent-config` page
- [ ] Create `/app/(dashboard)/calls` page
- [ ] Create `/app/(dashboard)/analytics` page
- [ ] Add navigation items to sidebar
- [ ] Create placeholder components for each page

**Day 4: Database Extensions**
- [ ] Add custom migration for agent tables
- [ ] Create `customers` table (links to teams)
- [ ] Create `agent_configs` table
- [ ] Create `practitioners` table
- [ ] Test that SaaS Starter tables still work
- [ ] Verify user signup and team creation

**Day 5: API Client Setup**
- [ ] Create `/lib/agent-api.ts` for FastAPI calls
- [ ] Set up environment variable for FastAPI URL
- [ ] Create TypeScript types for agent responses
- [ ] Add error handling utilities
- [ ] Test connection to FastAPI (when ready)

#### Backend Tasks (FastAPI)

**Day 1-2: Repository Setup**
- [ ] Create new repository: `jane-voice-agent-backend`
- [ ] FastAPI boilerplate project structure
  ```
  backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── api/
  │   ├── agents/
  │   ├── db/
  │   └── integrations/
  ├── requirements.txt
  └── Dockerfile
  ```
- [ ] Basic FastAPI app with health check endpoint
- [ ] Configure CORS for Next.js frontend

**Day 3-4: Database Connection**
- [ ] Configure SQLAlchemy to connect to shared PostgreSQL
- [ ] Create models for custom tables
- [ ] Test database connection
- [ ] Create initial migration for agent tables
- [ ] Ensure no conflicts with SaaS Starter tables

**Day 5: Docker & Local Development**
- [ ] Docker Compose setup for FastAPI
- [ ] Connect to shared local PostgreSQL
- [ ] Hot reload configuration
- [ ] Test API from Next.js frontend
- [ ] Document local development setup

#### DevOps Tasks

**Day 1-3: AWS Infrastructure**
- [ ] Create AWS account (production)
- [ ] Set up VPC with public/private subnets
- [ ] Provision RDS PostgreSQL (shared database)
  - [ ] Configure for both Next.js and FastAPI access
  - [ ] Enable encryption at rest
  - [ ] Set up automated backups
- [ ] Set up ElastiCache Redis
- [ ] Configure S3 buckets (documents, backups)
- [ ] Set up Secrets Manager

**Day 4-5: CI/CD Pipelines**
- [ ] GitHub Actions for FastAPI:
  - [ ] Run tests on PR
  - [ ] Build Docker image
  - [ ] Push to ECR
  - [ ] Deploy to ECS staging
- [ ] Vercel setup for Next.js:
  - [ ] Connect GitHub repository
  - [ ] Configure environment variables
  - [ ] Test automatic deployments

#### Deliverables
- ✅ Next.js SaaS Starter running locally with customizations
- ✅ FastAPI backend repository initialized
- ✅ Shared PostgreSQL database with both table sets
- ✅ Basic communication between Next.js and FastAPI
- ✅ CI/CD deploying to staging environments

#### Success Criteria
- [ ] Can log in to customized dashboard
- [ ] Pricing page shows correct tiers
- [ ] New placeholder pages accessible
- [ ] FastAPI health check returns 200
- [ ] Both services connect to same database
- [ ] Staging deployments working

---

### Week 2: FastAPI Development & Integration

**Goals:**
- Authentication between Next.js and FastAPI working
- API integration layer complete
- Agent testing endpoint functional

#### Backend Tasks (FastAPI)

**Day 1-2: Authentication & Authorization**
- [ ] JWT validation middleware (verify tokens from Next.js)
- [ ] User/team context extraction from JWT
- [ ] Customer lookup by team_id
- [ ] Rate limiting with Redis
- [ ] Auth middleware tests

**Day 3-5: Core API Endpoints**
- [ ] Customer management endpoints:
  - [ ] `GET /api/customers/me` - Get customer by team_id
  - [ ] `PATCH /api/customers/me` - Update settings
  - [ ] `POST /api/customers/jane/connect` - Start OAuth
- [ ] Agent testing endpoint:
  - [ ] `POST /api/agents/test` - Send test message
  - [ ] Returns agent response
- [ ] Health check and status endpoints
- [ ] API documentation (auto-generated FastAPI docs)

#### Frontend Tasks (Next.js)

**Day 1-2: Agent API Client**
- [ ] Complete `agent-api.ts` with all methods
- [ ] Add authentication headers (JWT from SaaS Starter)
- [ ] Error handling and retry logic
- [ ] Loading states management
- [ ] Success/error toast notifications

**Day 3: Agent Configuration Page**
- [ ] System prompt textarea
- [ ] Voice settings form
- [ ] Business hours configuration
- [ ] Feature toggles (checkboxes)
- [ ] Save button with loading state
- [ ] Connect to FastAPI `PATCH /api/customers/me`

**Day 4: Agent Testing Playground**
- [ ] Chat interface component
- [ ] Message input field
- [ ] Message history display
- [ ] "Test Agent" button
- [ ] Connect to `POST /api/agents/test`
- [ ] Display agent responses

**Day 5: Dashboard Integration**
- [ ] Update main dashboard with real stats (when available)
- [ ] Add quick action buttons
- [ ] Link to new pages (knowledge base, agent config, etc.)
- [ ] Test navigation flow

#### Database Tasks

**Day 1-2: Migrations**
- [ ] Alembic setup for FastAPI migrations
- [ ] Create migration for agent tables
- [ ] Test migration up/down
- [ ] Seed script for test data

**Day 3-5: ORM Models**
- [ ] SQLAlchemy models for all custom tables
- [ ] Relationships between tables
- [ ] Helper methods on models
- [ ] Query optimization

#### Testing

**Day 5:**
- [ ] Integration test: Next.js → FastAPI
- [ ] Test authentication flow
- [ ] Test API error handling
- [ ] Load test basic endpoints

#### Deliverables
- ✅ FastAPI exposing working endpoints
- ✅ Next.js successfully calling FastAPI
- ✅ Agent testing playground functional
- ✅ Agent configuration saving to database

#### Success Criteria
- [ ] Can configure agent from dashboard
- [ ] Can test agent and get responses
- [ ] JWT authentication working between services
- [ ] Database migrations applied successfully
- [ ] All tests passing

---

### Week 3: Jane App Integration

**Goals:**
- OAuth flow with Jane working
- Able to fetch practitioners, services, availability
- Basic sync mechanism

#### Backend Tasks

**Day 1-2: Jane OAuth**
- [ ] Register OAuth app with Jane
- [ ] OAuth callback endpoint
- [ ] Token exchange logic
- [ ] Store encrypted tokens in database
- [ ] Token refresh mechanism

**Day 3-5: Jane API Client**
- [ ] Python client class for Jane API
- [ ] Get practitioners endpoint
- [ ] Get services endpoint
- [ ] Get availability endpoint
- [ ] Create appointment endpoint
- [ ] Find/create patient endpoint
- [ ] Error handling and retries
- [ ] Rate limiting logic
- [ ] Caching layer (Redis)

#### Frontend Tasks

**Day 1-3: Jane Connection Flow**
- [ ] "Connect Jane" button/page
- [ ] OAuth redirect handling
- [ ] Connection status display
- [ ] Sync status indicator
- [ ] Disconnect Jane option

**Day 4-5: Data Display**
- [ ] Display practitioners list
- [ ] Display services list
- [ ] Show last sync time
- [ ] Manual sync trigger button

#### Testing
- [ ] OAuth flow end-to-end test
- [ ] Jane API client unit tests
- [ ] Test with Jane sandbox environment

#### Deliverables
- ✅ Jane OAuth working
- ✅ Can fetch and display Jane data
- ✅ Data cached appropriately

---

## Phase 2: Text Chat Agent (Weeks 4-6)

### Week 4: Knowledge Base & RAG

**Goals:**
- Pinecone integration
- Document processing pipeline
- RAG search working

#### Backend Tasks

**Day 1-2: Pinecone Setup**
- [ ] Create Pinecone account
- [ ] Initialize index
- [ ] Namespace strategy implementation
- [ ] OpenAI embeddings integration
- [ ] Vector upsert logic

**Day 3-5: Knowledge Base Service**
- [ ] Knowledge base manager class
- [ ] Add document endpoint
- [ ] Search endpoint
- [ ] Sync from Jane (auto-populate KB)
- [ ] Document upload handling (PDF, Word)
- [ ] Text extraction (PyPDF2, python-docx)
- [ ] Intelligent chunking
- [ ] Metadata management

#### Frontend Tasks

**Day 1-3: Knowledge Base UI**
- [ ] Knowledge base management page
- [ ] Auto-sync status display
- [ ] Manual document upload
- [ ] FAQ builder component
- [ ] Practice info form

**Day 4-5: Document Management**
- [ ] Document list view
- [ ] Upload progress indicator
- [ ] Preview/edit documents
- [ ] Delete documents
- [ ] Search knowledge base

#### Testing
- [ ] Upload various document types
- [ ] Test RAG search accuracy
- [ ] Benchmark embedding speed

#### Deliverables
- ✅ Knowledge base populated with Jane data
- ✅ Documents can be uploaded
- ✅ RAG search returns relevant results

---

### Week 5: Agno Agent Implementation

**Goals:**
- Agno framework integrated
- Basic agent responding to text
- Tools connected to Jane API

#### Backend Tasks

**Day 1-2: Agno Setup**
- [ ] Install Agno framework
- [ ] AgentOS boilerplate
- [ ] Basic agent configuration
- [ ] PostgreSQL connection for sessions

**Day 3-5: Agent Development**
- [ ] Multi-tenant agent manager
- [ ] Agent initialization logic
- [ ] System prompt templates
- [ ] Tool functions:
  - [ ] check_availability
  - [ ] book_appointment
  - [ ] answer_question (RAG)
- [ ] Session management
- [ ] Agent testing endpoint

#### Frontend Tasks

**Day 1-3: Agent Configuration UI**
- [ ] System prompt editor
- [ ] Voice settings selector
- [ ] Business hours configuration
- [ ] Enabled features toggles

**Day 4-5: Agent Testing Playground**
- [ ] Chat interface for testing
- [ ] Display tool calls
- [ ] Show knowledge base hits
- [ ] Debug panel

#### Testing
- [ ] Test agent with various intents
- [ ] Verify tool execution
- [ ] Check RAG integration
- [ ] Load test agent initialization

#### Deliverables
- ✅ Agent responds to text messages
- ✅ Can book appointments via text
- ✅ RAG integrated into responses

---

### Week 6: Chat Widget

**Goals:**
- Embeddable chat widget ready
- WebSocket real-time communication
- Working end-to-end booking flow

#### Frontend Tasks

**Day 1-3: Chat Widget Development**
- [ ] Standalone React chat component
- [ ] WebSocket connection
- [ ] Message list with auto-scroll
- [ ] Input field with send button
- [ ] Typing indicators
- [ ] Embed code generator
- [ ] Styling and theming

**Day 4-5: Widget Integration**
- [ ] Web Component wrapper
- [ ] CDN hosting setup
- [ ] Installation instructions
- [ ] Customization options
- [ ] Mobile responsive design

#### Backend Tasks

**Day 1-2: WebSocket Server**
- [ ] WebSocket endpoint setup
- [ ] Connection management
- [ ] Message broadcasting
- [ ] Session association

**Day 3-5: Chat API Endpoints**
- [ ] Create session endpoint
- [ ] Send message endpoint
- [ ] Get history endpoint
- [ ] Session analytics logging

#### Testing
- [ ] End-to-end booking via chat
- [ ] Multiple concurrent sessions
- [ ] Widget on different websites
- [ ] Mobile browser testing

#### Deliverables
- ✅ Chat widget embeddable
- ✅ Real-time messaging working
- ✅ Complete booking flow tested

---

## Phase 3: Voice Integration (Weeks 7-9)

### Week 7: Twilio & Phone Setup

**Goals:**
- Twilio account configured
- Phone numbers provisioned
- Basic call routing working

#### Backend Tasks

**Day 1-2: Twilio Integration**
- [ ] Create Twilio account (HIPAA tier)
- [ ] Sign Business Associate Agreement
- [ ] Twilio SDK integration
- [ ] Number provisioning logic
- [ ] Webhook handler for incoming calls

**Day 3-5: Call Management**
- [ ] Call routing logic
- [ ] Customer identification by phone
- [ ] Call logging to database
- [ ] SMS sending (confirmations)
- [ ] Call status tracking
- [ ] Recording management (optional)

#### Frontend Tasks

**Day 1-3: Phone Number Management**
- [ ] Display assigned phone number
- [ ] Setup instructions page
- [ ] Test call button
- [ ] Call forwarding guide

**Day 4-5: Call Logs UI**
- [ ] Call history list
- [ ] Call details view
- [ ] Transcript display (when available)
- [ ] Filtering and search

#### Testing
- [ ] Test inbound call routing
- [ ] Verify customer lookup
- [ ] Test SMS sending
- [ ] Check call logging

#### Deliverables
- ✅ Phone numbers provisioned per customer
- ✅ Calls routed to backend
- ✅ SMS confirmations working

---

### Week 8: LiveKit Voice Pipeline

**Goals:**
- LiveKit deployed
- Voice pipeline working
- Agno agent connected to voice

#### Backend Tasks

**Day 1-2: LiveKit Setup**
- [ ] Deploy LiveKit server (cloud or self-hosted)
- [ ] Configure SIP trunking
- [ ] Generate access tokens
- [ ] Test basic voice connection

**Day 3-5: Voice Agent Integration**
- [ ] Bridge Agno agent to LiveKit
- [ ] Voice pipeline configuration:
  - [ ] STT (Deepgram)
  - [ ] LLM (Agno wrapper)
  - [ ] TTS (ElevenLabs)
  - [ ] VAD (Silero)
- [ ] Twilio → LiveKit connection
- [ ] Voice-specific prompts
- [ ] Interrupt handling

#### Testing
- [ ] End-to-end voice call test
- [ ] Latency measurement
- [ ] Speech recognition accuracy
- [ ] Voice quality assessment
- [ ] Background noise handling

#### Deliverables
- ✅ Voice calls working end-to-end
- ✅ Agent responds naturally by voice
- ✅ Booking via phone successful

---

### Week 9: Cross-Modal Sessions & Polish

**Goals:**
- Session continuity between chat and voice
- Voice quality optimization
- Performance tuning

#### Backend Tasks

**Day 1-2: Session Continuity**
- [ ] Unified session model
- [ ] Link chat and voice sessions
- [ ] Context preservation logic
- [ ] Handoff mechanism (chat → voice)

**Day 3-5: Optimization**
- [ ] Voice latency reduction
- [ ] Agent response speed tuning
- [ ] Caching optimization
- [ ] Database query optimization
- [ ] Error handling improvements

#### Frontend Tasks

**Day 1-3: Cross-Modal UI**
- [ ] "Call Me" button in chat widget
- [ ] Phone number input for callback
- [ ] Session continuity indicator
- [ ] Voice call initiation flow

**Day 4-5: Analytics Dashboard**
- [ ] Usage overview cards
- [ ] Call/chat volume charts
- [ ] Booking success rate
- [ ] Cost tracking display

#### Testing
- [ ] Test chat → voice handoff
- [ ] Load testing (concurrent users)
- [ ] Stress testing (peak loads)
- [ ] Security testing (penetration test)

#### Deliverables
- ✅ Seamless chat-to-voice handoff
- ✅ Performance benchmarks met
- ✅ Analytics dashboard functional

---

## Phase 4: Launch Preparation (Weeks 10-12)

### Week 10: Beta Testing & Bug Fixes

**Goals:**
- 5-10 beta customers onboarded
- Critical bugs identified and fixed
- Documentation complete

#### Tasks

**Day 1-2: Beta Recruitment**
- [ ] Identify beta candidates (Jane users)
- [ ] Create beta program landing page
- [ ] Onboarding guide for beta testers
- [ ] Feedback collection form

**Day 3-5: Beta Support**
- [ ] Onboard first 3 beta customers
- [ ] Daily check-ins with beta users
- [ ] Bug triage and prioritization
- [ ] Hot fixes deployed
- [ ] Document common issues

#### Documentation
- [ ] User guide (getting started)
- [ ] Knowledge base setup guide
- [ ] FAQ for customers
- [ ] Troubleshooting guide
- [ ] API documentation (if exposing)

#### Deliverables
- ✅ 5+ beta customers active
- ✅ Major bugs fixed
- ✅ Documentation complete

---

### Week 11: Polish & Compliance

**Goals:**
- HIPAA compliance review
- UI/UX polish
- Performance optimization

#### Compliance Tasks
- [ ] HIPAA security risk assessment
- [ ] Review all BAAs (Twilio, OpenAI, AWS, etc.)
- [ ] Audit logging verification
- [ ] Encryption validation (at rest, in transit)
- [ ] Access control review
- [ ] Incident response plan documented
- [ ] Privacy policy and terms of service

#### Polish Tasks
- [ ] UI consistency pass
- [ ] Error messages user-friendly
- [ ] Loading states polished
- [ ] Mobile optimization
- [ ] Accessibility improvements
- [ ] Onboarding flow refinement

#### Performance
- [ ] Load testing results analysis
- [ ] Performance bottlenecks addressed
- [ ] Caching strategy refined
- [ ] Database indexes optimized

#### Deliverables
- ✅ HIPAA compliance checklist complete
- ✅ UI polished and consistent
- ✅ Performance targets met

---

### Week 12: Launch Preparation

**Goals:**
- Production environment ready
- Marketing site live
- Launch plan executed

#### Infrastructure
- [ ] Production AWS environment scaled
- [ ] Monitoring dashboards configured
- [ ] Alerting rules set up
- [ ] Backup verification
- [ ] Disaster recovery tested
- [ ] Status page configured

#### Marketing Site
- [ ] Landing page design
- [ ] Product demo video
- [ ] Pricing page
- [ ] Sign-up flow
- [ ] Email capture
- [ ] Analytics tracking (Plausible/Fathom)

#### Launch Activities
- [ ] Soft launch announcement (email, social)
- [ ] Product Hunt submission
- [ ] Post in Jane App user groups
- [ ] Direct outreach to prospects
- [ ] Blog post about launch
- [ ] PR outreach (healthcare tech press)

#### Support Readiness
- [ ] Support email setup
- [ ] Help documentation live
- [ ] Customer onboarding checklist
- [ ] Billing system tested (Stripe)
- [ ] Refund policy established

#### Deliverables
- ✅ Production environment stable
- ✅ Marketing site live
- ✅ Launch executed
- ✅ First paying customers

---

## Risk Management

### High-Priority Risks

**Risk 1: Jane API Integration Issues**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:** 
  - Get sandbox access early
  - Regular testing with Jane
  - Build mock Jane API for testing
  - Fallback manual booking flow
- **Owner:** Backend Lead

**Risk 2: Voice Quality/Latency Problems**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:**
  - Prototype voice early (Week 4)
  - Multiple STT/TTS provider testing
  - Performance benchmarking
  - Budget for premium voice services
- **Owner:** Backend Lead

**Risk 3: HIPAA Compliance Gaps**
- **Probability:** Low
- **Impact:** Critical
- **Mitigation:**
  - Compliance consultant (Week 1)
  - Regular security audits
  - BAAs signed before launch
  - Legal review of all processes
- **Owner:** Randy

**Risk 4: Team Bandwidth/Availability**
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:**
  - Clear prioritization
  - Scope flexibility (cut features if needed)
  - Contractor support available
  - Realistic timeline buffers
- **Owner:** Randy

**Risk 5: Beta Customer Acquisition**
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:**
  - Start recruiting Week 1
  - Offer incentives (free months)
  - Personal network outreach
  - Jane user group engagement
- **Owner:** Randy

---

## Success Criteria

### Week 3 Checkpoint
- [ ] Jane OAuth working
- [ ] Database schema deployed
- [ ] Team productive and unblocked

**Go/No-Go Decision:** Proceed to Phase 2

### Week 6 Checkpoint
- [ ] Text chat agent booking appointments
- [ ] Knowledge base functional
- [ ] At least 1 internal demo successful

**Go/No-Go Decision:** Proceed to Phase 3

### Week 9 Checkpoint
- [ ] Voice calls working end-to-end
- [ ] Voice quality acceptable (<500ms latency)
- [ ] Cross-modal sessions functional

**Go/No-Go Decision:** Proceed to Phase 4

### Week 12 Launch Criteria
- [ ] 5+ beta customers giving positive feedback
- [ ] <10 critical bugs in backlog
- [ ] HIPAA compliance validated
- [ ] Marketing site live
- [ ] Billing system working
- [ ] Support processes in place

**Go/No-Go Decision:** Launch publicly

---

## Dependencies & Prerequisites

### External Dependencies

**Week 1:**
- [ ] AWS account approved
- [ ] GitHub organization created
- [ ] Domain name purchased

**Week 3:**
- [ ] Jane App OAuth credentials obtained
- [ ] Jane sandbox environment access

**Week 4:**
- [ ] Pinecone account created
- [ ] OpenAI API access confirmed

**Week 7:**
- [ ] Twilio account approved (HIPAA tier)
- [ ] Twilio BAA signed

**Week 8:**
- [ ] LiveKit account or self-hosted instance
- [ ] Deepgram API access
- [ ] ElevenLabs API access

**Week 11:**
- [ ] Legal review of terms/privacy policy
- [ ] Compliance consultant engaged

### Team Dependencies

**Continuous:**
- Randy available for product decisions
- Daily standups (15 min)
- Weekly sprint planning (1 hour)
- Bi-weekly retrospectives

**Critical Path:**
- Backend must complete Jane integration (Week 3) before KB work (Week 4)
- Chat must work (Week 6) before voice (Week 8)
- Beta testing (Week 10) must inform polish (Week 11)

---

## Budget Estimate (12 Weeks)

### Personnel
- 2 Full-Stack Engineers × 12 weeks × $10k/week = $240k
- 1 Frontend Engineer × 12 weeks × $8k/week = $96k
- 0.5 DevOps Engineer × 12 weeks × $6k/week = $36k
- **Total Personnel: $372k**

### Infrastructure (Estimated)
- AWS (dev, staging, prod): $2k/month × 3 = $6k
- Pinecone: $70/month × 3 = $210
- Twilio (testing): $500 × 3 = $1.5k
- OpenAI API: $1k × 3 = $3k
- Deepgram/ElevenLabs: $1k × 3 = $3k
- Misc services: $1k × 3 = $3k
- **Total Infrastructure: ~$17k**

### Services & Tools
- Design contractor: $5k (Weeks 1-2)
- Legal/compliance: $10k
- Monitoring/tools: $1k
- **Total Services: ~$16k**

### Contingency (15%)
- **$60k**

### **Total Budget: ~$465k**

---

## Post-Launch Roadmap (Months 4-6)

### Month 4: Stabilization
- Monitor production performance
- Fix bugs reported by customers
- Improve onboarding based on feedback
- Optimize costs

### Month 5: Payment Features
- Add payment handling tools
- Invoice status checking
- Payment link generation
- Stripe integration

### Month 6: Advanced Features
- Sub-agent architecture for multi-practitioner clinics
- Advanced analytics dashboard
- Email/SMS automation
- Improved document processing

---

## Communication Plan

### Daily
- **Standup:** 10am, 15 minutes
- **Slack:** Primary communication
- **Blocker resolution:** Same day

### Weekly
- **Sprint Planning:** Monday, 1 hour
- **Demo:** Friday, 30 minutes
- **Team Sync:** Wednesday, 30 minutes

### Bi-weekly
- **Retrospective:** Every other Friday
- **Stakeholder Update:** Report to Randy

### Monthly
- **All-hands:** Progress review
- **Roadmap Review:** Adjust based on learnings

---

## Definition of Done

### Feature Complete
- [ ] Code written and reviewed
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] Documented in code
- [ ] User-facing docs updated
- [ ] Deployed to staging
- [ ] QA tested
- [ ] Product owner approved

### Sprint Complete
- [ ] All committed stories done
- [ ] No critical bugs
- [ ] Demo delivered
- [ ] Retrospective held

### Phase Complete
- [ ] All phase goals met
- [ ] Checkpoint criteria satisfied
- [ ] Go/No-Go decision made
- [ ] Next phase kicked off

---

## Appendix

### Development Practices

**Code Review:**
- All PRs require 1 approval
- Automated checks must pass
- Review within 24 hours

**Testing:**
- Unit tests required for new code
- Integration tests for critical paths
- E2E tests for user flows
- Load testing before launch

**Deployment:**
- Merge to `develop` → auto-deploy to staging
- Merge to `main` → manual deploy to production
- Feature flags for risky changes

### Tools & Accounts Needed

**Development:**
- [ ] GitHub organization
- [ ] Figma (design)
- [ ] Postman (API testing)
- [ ] Slack workspace

**Infrastructure:**
- [ ] AWS account (production)
- [ ] AWS account (staging)
- [ ] Terraform Cloud
- [ ] Domain registrar

**Third-Party Services:**
- [ ] Pinecone
- [ ] OpenAI
- [ ] Twilio
- [ ] Deepgram
- [ ] ElevenLabs
- [ ] SendGrid
- [ ] Stripe

**Monitoring:**
- [ ] Sentry
- [ ] CloudWatch (included in AWS)
- [ ] Status page (e.g., Statuspage.io)

---

**Document Status:** Draft v1.0  
**Next Review:** Week 1 (after team onboarding)  
**Owner:** Randy
