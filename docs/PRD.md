# Product Requirements Document (PRD)
# Jane AI Voice & Chat Agent SaaS

**Version:** 1.0  
**Date:** November 22, 2025  
**Owner:** Randy  
**Status:** Draft

---

## Executive Summary

A SaaS platform that enables Jane App practitioners to deploy AI-powered voice and text chat agents that handle appointment scheduling, payment processing, and customer support. The platform provides a white-label solution specifically designed for healthcare practices using Jane App.

---

## Problem Statement

### Current Pain Points

**For Healthcare Practices:**
- Staff spend 40-60% of time on phone scheduling and rescheduling
- After-hours calls go to voicemail, leading to lost appointments
- Payment follow-ups are time-consuming and awkward
- Common questions (hours, location, services) answered repeatedly
- Small practices (1-5 practitioners) can't afford full-time reception

**For Patients:**
- Long wait times on hold during business hours
- No ability to book outside office hours
- Frustration with voicemail tag
- Unclear payment policies and processes

### Market Opportunity

- Jane App has 10,000+ practices across North America
- Healthcare practices pay $99-199/month for Jane already
- They understand value of automation and efficiency tools
- Underserved market: most voice AI solutions target enterprise, not healthcare SMBs

---

## Product Vision

**Mission Statement:**  
Empower healthcare practitioners to provide 24/7 patient support through intelligent, HIPAA-compliant AI agents that seamlessly integrate with their existing Jane App workflow.

**Success Vision (12 months):**  
500 practices using our platform, handling 50,000+ patient interactions monthly, with 85%+ customer satisfaction and <5% churn rate.

---

## Target Users

### Primary User: Practice Owner/Office Manager
**Demographics:**
- Healthcare practitioners (chiropractors, physiotherapists, massage therapists, counselors)
- Small to medium practices (1-10 practitioners)
- Already using Jane App for practice management
- Tech-savvy enough to use Jane but not developers

**Goals:**
- Reduce administrative overhead
- Improve patient experience
- Increase appointment booking conversion
- Extend hours without adding staff costs
- Streamline payment collections

**Pain Points:**
- Limited budget for staff
- After-hours missed opportunities
- Manual repetitive tasks
- Patient satisfaction concerns

### Secondary User: Patient/Caller
**Demographics:**
- Seeking healthcare services
- Mixed technical comfort levels
- Ages 25-65 primarily
- Expect modern, responsive service

**Goals:**
- Book appointments quickly
- Get questions answered immediately
- Make payments easily
- Receive care without friction

---

## Core Features

### Phase 1: MVP (Weeks 1-12)

#### 1. Customer Dashboard
**Priority:** P0  
**User Story:** As a practice owner, I want a central dashboard to manage my AI agent settings and view activity.

**Features:**
- Practice account creation and setup
- Jane App OAuth connection
- Basic agent configuration (greetings, business rules)
- Call/chat activity logs
- Usage metrics (minutes used, calls handled)
- Billing and subscription management

**Acceptance Criteria:**
- User can sign up and connect Jane in <5 minutes
- Dashboard loads in <2 seconds
- Real-time activity updates
- Mobile-responsive design

#### 2. Knowledge Base Management
**Priority:** P0  
**User Story:** As a practice owner, I want to teach my AI agent about my practice so it answers accurately.

**Features:**
- Auto-sync from Jane App (practitioners, services, locations)
- Practice info input (philosophy, specialties, policies)
- Per-practitioner details
- FAQ builder with suggested questions
- Document upload (PDF, Word, text files)
- Knowledge base preview and testing

**Acceptance Criteria:**
- Jane sync completes in <30 seconds
- Support PDFs up to 10MB
- FAQ builder with drag-and-drop reordering
- Search/preview knowledge base content

#### 3. Text Chat Widget
**Priority:** P0  
**User Story:** As a patient, I want to chat with the practice online to book appointments or ask questions.

**Features:**
- Embeddable chat widget for practice website
- Mobile and desktop responsive
- Support for:
  - Appointment scheduling
  - Service inquiries
  - Office hours and location
  - Payment questions
- Session persistence
- Typing indicators and read receipts
- Handoff to human option

**Acceptance Criteria:**
- Widget loads in <1 second
- Works on mobile and desktop
- Correctly handles 90%+ of booking intents
- Escalation to human when needed
- HIPAA-compliant conversation handling

#### 4. Voice Call Handling
**Priority:** P0  
**User Story:** As a practice owner, I want patients to call and interact with an AI agent that sounds professional and helpful.

**Features:**
- Dedicated Twilio phone number per practice
- Call forwarding setup instructions
- Natural voice conversation with:
  - Appointment booking
  - Availability checking
  - Rescheduling/cancellations
  - General questions
- Real-time speech recognition
- Natural, professional voice synthesis
- Call recording (optional, with consent)
- Session continuity from chat to voice

**Acceptance Criteria:**
- <200ms voice latency
- 95%+ speech recognition accuracy
- Natural-sounding voice output
- Handles interruptions gracefully
- Successfully books appointments 85%+ of the time

#### 5. Jane App Integration
**Priority:** P0  
**User Story:** As a practice owner, I want the AI agent to seamlessly book appointments in my Jane calendar.

**Features:**
- OAuth 2.0 authentication with Jane
- Real-time availability checking
- Appointment creation with patient details
- Patient lookup and creation
- Service selection and pricing
- Practitioner assignment
- Appointment confirmations via SMS/email
- Cancellation and rescheduling

**Acceptance Criteria:**
- Sync with Jane in real-time (<5 second delay)
- Handle double-booking prevention
- Support multiple practitioners
- Accurate pricing display
- Proper error handling for API failures

#### 6. Multi-Tenant Agent System
**Priority:** P0  
**User Story:** As the platform operator, I need to run isolated agents for each practice efficiently.

**Features:**
- Customer isolation (data, sessions, knowledge)
- Shared infrastructure, isolated context
- Dynamic agent configuration per customer
- Session management across modalities
- Tool execution with customer-specific credentials
- RAG search with namespaced knowledge bases

**Acceptance Criteria:**
- Zero data leakage between customers
- Agent initialization <3 seconds
- Support 100+ concurrent calls
- Horizontal scalability
- HIPAA-compliant data isolation

### Phase 2: Enhanced Features (Months 3-6)

#### 7. Payment Handling
**Priority:** P1  
**User Story:** As a practice owner, I want my AI agent to handle payment inquiries and send payment links.

**Features:**
- Check outstanding invoice status in Jane
- Send payment links via SMS/email
- Payment confirmation
- Payment plan information
- Insurance coverage questions

**Acceptance Criteria:**
- Retrieve invoice data from Jane
- Generate secure payment links
- Track payment status
- Handle payment-related FAQs

#### 8. Sub-Agent Architecture
**Priority:** P1  
**User Story:** As a practice with multiple specialists, I want personalized agents for each practitioner.

**Features:**
- Practitioner-specific greetings
- Custom system prompts per practitioner
- Filtered tools and knowledge
- Routing logic based on patient request
- Seamless handoff between sub-agents

**Acceptance Criteria:**
- Support up to 10 practitioners per practice
- <1 second handoff between sub-agents
- Maintain conversation context during handoff
- Practitioner-specific voice/personality options

#### 9. Advanced Analytics
**Priority:** P1  
**User Story:** As a practice owner, I want detailed insights into my AI agent's performance.

**Features:**
- Call/chat volume trends
- Booking conversion rates
- Common patient questions
- Agent accuracy metrics
- Cost analysis
- Patient satisfaction scores
- Peak usage times
- Export reports (CSV, PDF)

**Acceptance Criteria:**
- Real-time dashboard updates
- Historical data for 12+ months
- Customizable date ranges
- Downloadable reports

#### 10. Advanced RAG & Document Processing
**Priority:** P1  
**User Story:** As a practice owner, I want to upload my existing documents so the agent can reference them.

**Features:**
- Bulk document upload
- Intelligent text extraction
- Semantic chunking
- Multi-document search
- Source attribution in responses
- Document versioning
- Knowledge base analytics (most referenced docs)

**Acceptance Criteria:**
- Support 100+ documents per practice
- Process 10MB PDF in <10 seconds
- Accurate source citations
- Search relevance >90%

### Phase 3: Advanced Features (Months 6-12)

#### 11. Multi-Location Support
**Priority:** P2

#### 12. Insurance Verification
**Priority:** P2

#### 13. Waitlist Management
**Priority:** P2

#### 14. White-Label Options
**Priority:** P2

#### 15. API for Third-Party Integrations
**Priority:** P2

---

## User Stories & Acceptance Criteria

### Epic 1: Onboarding

**US-1.1: Quick Setup**  
*As a practice owner, I want to set up my AI agent in under 10 minutes.*

**Acceptance Criteria:**
- Sign-up flow with email/password
- Jane OAuth connection (1-click)
- Auto-import practice data
- Basic configuration wizard
- Test call/chat before going live
- Total time: <10 minutes

**US-1.2: Knowledge Base Training**  
*As a practice owner, I want to easily teach my agent about my practice.*

**Acceptance Criteria:**
- Guided input form for practice info
- FAQ suggestions based on specialty
- Document upload with preview
- Test agent responses in real-time
- Knowledge completeness indicator

### Epic 2: Patient Interaction

**US-2.1: Book Appointment via Chat**  
*As a patient, I want to book an appointment through the chat widget on the practice website.*

**Flow:**
1. Patient opens chat widget
2. Agent greets and asks how to help
3. Patient requests appointment
4. Agent asks for service type
5. Agent shows available times
6. Patient selects time
7. Agent collects name and phone
8. Agent confirms booking
9. Patient receives SMS confirmation

**Acceptance Criteria:**
- Complete flow in <3 minutes
- Handle date/time ambiguity
- Prevent double-booking
- Send confirmation within 30 seconds

**US-2.2: Book Appointment via Phone**  
*As a patient, I want to call and book an appointment naturally by voice.*

**Flow:**
1. Patient calls practice number (forwarded)
2. Agent answers with custom greeting
3. Natural conversation about availability
4. Agent books appointment in Jane
5. Agent confirms verbally
6. SMS confirmation sent

**Acceptance Criteria:**
- Answer call in <3 rings
- Natural conversation flow
- Handle accents and background noise
- 85%+ successful booking rate
- <5 minute average call duration

**US-2.3: Cross-Modal Session**  
*As a patient, I want to start in chat and then call without repeating myself.*

**Flow:**
1. Patient starts chat about booking
2. Patient clicks "Call Instead"
3. Agent calls patient's number
4. Agent references chat history
5. Continues conversation seamlessly

**Acceptance Criteria:**
- Session ID carried over
- Agent remembers previous context
- No need to repeat information
- <30 second call initiation

### Epic 3: Practice Management

**US-3.1: View Call Activity**  
*As a practice owner, I want to see all calls and chats handled by my agent.*

**Acceptance Criteria:**
- List view with filters (date, outcome, duration)
- Transcript/summary view
- Listen to call recordings (if enabled)
- Export to CSV
- Search by patient name/phone

**US-3.2: Monitor Usage & Billing**  
*As a practice owner, I want to track my usage and costs.*

**Acceptance Criteria:**
- Real-time minute counter
- Cost projection for current month
- Usage alerts (80%, 100% of plan)
- Upgrade/downgrade plan options
- Billing history and invoices

---

## Technical Requirements

### Performance

- **Response Time:** <200ms for text responses, <500ms for voice
- **Availability:** 99.5% uptime SLA
- **Scalability:** Support 1000+ practices, 10,000+ concurrent sessions
- **Voice Latency:** <200ms end-to-end
- **Agent Initialization:** <3 seconds

### Security & Compliance

- **HIPAA Compliance:** Full compliance with signed BAAs
- **Data Encryption:** TLS 1.3 in transit, AES-256 at rest
- **Access Control:** Role-based with MFA support
- **Audit Logging:** All PHI access logged with 6-year retention
- **Data Isolation:** Complete separation between customers
- **Secure Credentials:** Encrypted storage with KMS

### Integrations

- **Jane App API:** Full OAuth 2.0 integration
- **Twilio:** Voice and SMS
- **Payment Processors:** Stripe (future)
- **Email:** SendGrid or AWS SES
- **Analytics:** Custom dashboards

---

## Success Metrics

### Primary KPIs

**Customer Acquisition:**
- Target: 50 practices in first 3 months
- Target: 500 practices by month 12
- Customer Acquisition Cost (CAC): <$500
- Conversion rate: >20% (trial to paid)

**Customer Success:**
- Net Revenue Retention: >100%
- Churn rate: <5% monthly
- Customer Satisfaction (CSAT): >4.5/5
- Net Promoter Score (NPS): >50

**Product Performance:**
- Booking success rate: >85%
- Voice call completion rate: >90%
- Agent accuracy: >95%
- Average response time: <2 seconds

**Business Metrics:**
- Monthly Recurring Revenue (MRR) growth: >20%/month
- Gross margin: >65%
- Average Revenue Per User (ARPU): $150-200/month

### Secondary Metrics

- Average calls/chats per practice per month
- Minutes usage per practice
- Knowledge base completeness
- Time to first booking
- Patient satisfaction with AI interactions

---

## Go-to-Market Strategy

### Target Market Segmentation

**Tier 1: Early Adopters (Months 1-3)**
- Tech-savvy solo practitioners
- Chiropractors and physiotherapists
- Practices with high call volume
- Already frustrated with phone management

**Tier 2: Growth Segment (Months 4-9)**
- Multi-practitioner clinics (2-5 people)
- Massage therapy and wellness centers
- Mental health counselors
- Practices expanding locations

**Tier 3: Enterprise (Months 10+)**
- Large clinics (5-10+ practitioners)
- Multi-location practices
- Franchise operations

### Distribution Channels

1. **Jane App Marketplace** (if available)
   - Official integration listing
   - Featured in Jane newsletter

2. **Direct Outreach**
   - Email campaigns to Jane users
   - LinkedIn targeting practice owners

3. **Content Marketing**
   - SEO: "Jane App automation", "AI receptionist for chiropractors"
   - Case studies and testimonials
   - YouTube demos

4. **Community Engagement**
   - Facebook groups for Jane users
   - Healthcare practice management forums
   - Conference sponsorships

5. **Partnerships**
   - Jane App co-marketing
   - Practice management consultants
   - Healthcare coaching programs

### Pricing Strategy

**Starter Plan: $99/month**
- 200 minutes included
- Text chat + voice calls
- Up to 3 practitioners
- Basic knowledge base
- Email support
- $0.50 per additional minute

**Professional Plan: $199/month**
- 500 minutes included
- All Starter features
- Payment handling
- Sub-agent support (up to 10 practitioners)
- Advanced analytics
- Priority support
- $0.45 per additional minute

**Enterprise Plan: $399/month**
- 1500 minutes included
- All Professional features
- Custom integrations
- White-label options
- Multi-location support
- Dedicated account manager
- Custom pricing for overages

**Add-ons:**
- Additional phone numbers: $10/month
- Call recording: $20/month
- Advanced reporting: $30/month

---

## Competitive Analysis

### Direct Competitors

**1. Vapi (via third-party developers)**
- Strength: Polished platform, easy setup
- Weakness: Not healthcare-specific, no Jane integration, more expensive
- Our Advantage: Native Jane integration, healthcare focus, better pricing

**2. Generic AI Chatbots (Drift, Intercom)**
- Strength: Established brands, feature-rich
- Weakness: No voice, no healthcare focus, no Jane integration
- Our Advantage: Voice + text, healthcare UX, deep Jane integration

**3. Virtual Receptionist Services (Ruby Receptionists)**
- Strength: Human touch, established trust
- Weakness: Expensive ($300-800/month), limited hours, manual
- Our Advantage: 24/7, instant response, lower cost, Jane integration

### Market Positioning

**Our Unique Value Proposition:**
"The only AI voice and chat assistant built specifically for Jane App practices - handle appointments, payments, and patient questions 24/7 with HIPAA-compliant technology."

**Key Differentiators:**
1. Native Jane App integration (only solution with OAuth)
2. Healthcare-specific (HIPAA compliant from day one)
3. Dual modality (voice + text) with session continuity
4. Healthcare SMB pricing (not enterprise-only)
5. Purpose-built for practice workflows

---

## Risks & Mitigation

### Technical Risks

**Risk:** Jane App API changes/deprecation  
**Mitigation:** Regular API monitoring, maintain communication with Jane, fallback modes

**Risk:** Voice AI quality issues (accents, noise)  
**Mitigation:** Multiple STT/TTS providers, continuous testing, human fallback option

**Risk:** HIPAA compliance gaps  
**Mitigation:** Legal review, penetration testing, compliance automation (Vanta/Drata)

**Risk:** Scalability bottlenecks  
**Mitigation:** Load testing, horizontal scaling architecture, CDN usage

### Business Risks

**Risk:** Jane App competition/partnership refusal  
**Mitigation:** Focus on customer value, build defensible IP, explore other healthcare platforms

**Risk:** Low customer acquisition  
**Mitigation:** Beta program with discounts, referral incentives, money-back guarantee

**Risk:** High churn due to poor AI performance  
**Mitigation:** Intensive beta testing, continuous improvement, proactive support

**Risk:** Legal/regulatory challenges in healthcare AI  
**Mitigation:** Legal counsel, insurance, clear disclaimers, human oversight options

### Market Risks

**Risk:** Market too small or not ready for AI  
**Mitigation:** Adjacent market expansion (other EMRs), feature evolution based on feedback

**Risk:** Pricing too high/low  
**Mitigation:** A/B test pricing, usage-based flexibility, grandfather early adopters

---

## Launch Plan

### Beta Phase (Weeks 1-4)

**Goal:** Validate core functionality with 5-10 friendly practices

**Activities:**
- Recruit beta testers (offer free 3 months)
- Deploy MVP with text chat
- Weekly feedback sessions
- Rapid iteration on feedback
- Document common issues

**Success Criteria:**
- 80%+ positive feedback
- <5 critical bugs
- At least 50 successful bookings
- 3+ practices willing to pay

### Soft Launch (Weeks 5-8)

**Goal:** Expand to 25-50 paying customers

**Activities:**
- Add voice calling functionality
- Launch basic marketing site
- Enable self-service signup
- Implement billing
- Start content marketing

**Success Criteria:**
- 25+ paying customers
- <10% churn
- 85%+ booking success rate
- Revenue: $3-5k MRR

### Public Launch (Weeks 9-12)

**Goal:** Scale to 100-150 customers

**Activities:**
- Full marketing push
- Jane App marketplace listing (if available)
- PR outreach
- Webinar series
- Referral program launch

**Success Criteria:**
- 100+ paying customers
- <5% churn
- $15-20k MRR
- 4.5+ star rating

---

## Open Questions

1. Does Jane App have an official app marketplace or partner program?
2. What are Jane's API rate limits and costs?
3. Should we offer a free trial, and if so, how long?
4. Do we need a medical advisor for marketing/positioning?
5. What insurance/legal protection do we need for healthcare AI?
6. Should we support Jane competitors (Cliniko, SimplePractice) in Phase 2?
7. What is the minimum viable knowledge base for a practice?
8. Should we offer custom voice cloning for practitioners?

---

## Appendix

### Glossary

- **Jane App:** Cloud-based practice management software for healthcare practitioners
- **PHI:** Protected Health Information (HIPAA term)
- **BAA:** Business Associate Agreement (HIPAA requirement)
- **RAG:** Retrieval-Augmented Generation (AI technique for knowledge search)
- **Agno:** Multi-agent AI framework used for our agents
- **LiveKit:** Real-time voice communication platform

### References

- Jane App API Documentation: https://developers.jane.app
- HIPAA Compliance Guide: https://www.hhs.gov/hipaa
- Twilio HIPAA Documentation: https://www.twilio.com/legal/hipaa
- Agno Documentation: https://docs.agno.com

---

**Document Control:**
- Next Review Date: December 1, 2025
- Stakeholders: Randy (Product Owner), Engineering Team, Design Team
- Approval Status: Draft - Pending Final Review
