# Technical Architecture Document
# Jane AI Voice & Chat Agent SaaS

**Version:** 1.0  
**Date:** November 22, 2025  
**Author:** Randy  
**Status:** Draft

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Technology Stack](#technology-stack)
4. [System Architecture](#system-architecture)
5. [Component Design](#component-design)
6. [Data Architecture](#data-architecture)
7. [API Design](#api-design)
8. [Security Architecture](#security-architecture)
9. [Deployment Architecture](#deployment-architecture)
10. [Scalability & Performance](#scalability--performance)
11. [Monitoring & Observability](#monitoring--observability)
12. [Disaster Recovery](#disaster-recovery)

---

## System Overview

### Purpose

A HIPAA-compliant, multi-tenant SaaS platform that provides AI-powered voice and text chat agents for Jane App healthcare practices. The system handles appointment scheduling, payment inquiries, and customer support through both phone calls and web/mobile chat interfaces.

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Client Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │ Web Dashboard│  │ Chat Widget │  │  Phone Calls     │     │
│  │  (Next.js)   │  │  (React)    │  │  (Twilio)        │     │
│  │  SaaS Starter│  │             │  │                  │     │
│  └─────────────┘  └─────────────┘  └──────────────────┘     │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│              Next.js Frontend (SaaS Starter)                  │
│  - Authentication & User Management (pre-built)               │
│  - Stripe Billing Integration (pre-built)                    │
│  - Dashboard Layout (pre-built)                              │
│  - API Gateway to FastAPI Backend                            │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Agent Engine)                │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Multi-Tenant   │  │  Knowledge   │  │   Session      │  │
│  │  Agent Manager  │  │  Base (RAG)  │  │   Manager      │  │
│  │  (AgentOS)      │  │  (Pinecone)  │  │   (Redis)      │  │
│  └─────────────────┘  └──────────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                  Integration Layer                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Jane App    │  │   Twilio     │  │   Voice Pipeline │    │
│  │   OAuth     │  │   Voice/SMS  │  │   (LiveKit)      │    │
│  └─────────────┘  └──────────────┘  └──────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                     Data Layer (Shared)                       │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐    │
│  │  PostgreSQL  │  │    Redis    │  │    Pinecone      │    │
│  │  (Shared DB) │  │   (Cache)   │  │    (Vectors)     │    │
│  │  Users+Teams │  │             │  │                  │    │
│  │  +Agent Data │  │             │  │                  │    │
│  └──────────────┘  └─────────────┘  └──────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

**Key Architecture Decisions:**

1. **Next.js SaaS Starter for Frontend:**
   - Provides production-ready auth, billing, and dashboard
   - Saves 3-5 weeks of development time
   - Acts as API gateway to FastAPI backend

2. **FastAPI for Agent Engine:**
   - Handles all AI/agent operations
   - Python-native for ML/AI libraries
   - Separate deployment for scaling

3. **Shared PostgreSQL Database:**
   - Next.js owns: users, teams, subscriptions, activity logs
   - FastAPI owns: agents, calls, knowledge, sessions
   - Both services connect to same database

4. **Clean Separation:**
   - Frontend: User-facing features, auth, billing
   - Backend: Agent logic, voice/chat processing, integrations

---

## Architecture Principles

### 1. Multi-Tenancy First
- Complete data isolation between customers
- Shared infrastructure, isolated contexts
- Efficient resource utilization
- Horizontal scalability per tenant

### 2. HIPAA Compliance
- Encryption at rest and in transit
- Comprehensive audit logging
- Access controls and authentication
- Business Associate Agreements with all vendors
- Data residency and retention policies

### 3. Modular & Extensible
- Microservices-oriented where appropriate
- Clear separation of concerns
- Plugin architecture for integrations
- Easy to add new features without refactoring

### 4. Performance Optimized
- <200ms voice latency
- <2s text response time
- Efficient agent initialization
- Caching strategies
- Async operations

### 5. Reliability & Resilience
- 99.5% uptime target
- Graceful degradation
- Retry mechanisms
- Circuit breakers
- Health checks and auto-recovery

### 6. Developer Experience
- Infrastructure as Code
- Automated testing (unit, integration, E2E)
- CI/CD pipelines
- Comprehensive documentation
- Local development parity

---

## Technology Stack

### Frontend Technologies

**Customer Dashboard (Based on Next.js SaaS Starter):**
- **Foundation:** Next.js SaaS Starter (https://github.com/nextjs/saas-starter)
  - ✅ Pre-built auth system (email/password with JWTs)
  - ✅ Stripe integration for subscriptions
  - ✅ Dashboard layouts with CRUD operations
  - ✅ RBAC (Owner/Member roles)
  - ✅ Activity logging system
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript 5.3+
- **Styling:** Tailwind CSS 3.4 + shadcn/ui components (included in starter)
- **State Management:** 
  - TanStack Query (React Query) for server state
  - Zustand for client state (if needed beyond starter)
- **Forms:** React Hook Form + Zod validation (included in starter)
- **Auth:** JWT cookies (included in starter)
- **Charts:** Recharts or Tremor
- **Real-time:** WebSocket client for live updates
- **Database ORM:** Drizzle ORM (included in starter)

**Customizations to SaaS Starter:**
- Add knowledge base management pages
- Add agent configuration interface
- Add call/chat logs pages
- Add analytics dashboard
- Integrate with FastAPI backend for agent operations

**Chat Widget (Custom Build):**
- **Framework:** React 18
- **Build:** Vite for fast builds
- **Embeddable:** Web Component wrapper
- **Real-time:** WebSocket for chat
- **Voice:** WebRTC for browser-to-phone

### Backend Technologies

**API Server:**
- **Framework:** FastAPI 0.110+
- **Language:** Python 3.11+
- **Async Runtime:** uvicorn with uvloop
- **API Docs:** Auto-generated OpenAPI/Swagger
- **Validation:** Pydantic v2
- **Auth:** JWT tokens (PyJWT), OAuth 2.0

**Agent Framework:**
- **Core:** Agno 2.0+ (multi-agent framework)
- **LLM:** OpenAI GPT-4 Turbo (with fallback to Claude)
- **Embeddings:** OpenAI text-embedding-3-small
- **Voice Pipeline:** LiveKit Agents SDK
- **STT:** Deepgram Nova-2 (primary), AssemblyAI (fallback)
- **TTS:** ElevenLabs (professional), Cartesia (low latency)
- **VAD:** Silero VAD

**Background Jobs:**
- **Queue:** Celery 5.3+
- **Broker:** Redis
- **Tasks:** 
  - Document processing
  - Jane API sync
  - Email/SMS sending
  - Analytics aggregation

### Data Storage

**Primary Database:**
- **System:** PostgreSQL 15+
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Extensions:** pgcrypto, pg_trgm

**Caching:**
- **System:** Redis 7+
- **Use Cases:**
  - Session storage
  - Rate limiting
  - Jane API response cache
  - Celery broker

**Vector Database:**
- **System:** Pinecone (managed)
- **Alternative:** Supabase pgvector (if cost-sensitive)
- **Use Case:** Knowledge base embeddings, RAG search

**Object Storage:**
- **System:** AWS S3
- **Use Cases:**
  - Uploaded documents
  - Call recordings
  - Backups

### Infrastructure

**Cloud Provider:** AWS (HIPAA-compliant configuration)

**Compute:**
- **Containers:** Docker
- **Orchestration:** ECS Fargate (or EKS for scale)
- **Serverless:** AWS Lambda (webhooks, lightweight tasks)

**Networking:**
- **Load Balancer:** Application Load Balancer (ALB)
- **CDN:** CloudFront
- **DNS:** Route 53
- **VPC:** Private subnets for sensitive services

**Secrets Management:**
- **System:** AWS Secrets Manager
- **Alternative:** HashiCorp Vault

### Third-Party Services

**Voice & Messaging:**
- **Twilio:** Programmable Voice, SMS
- **LiveKit:** Real-time voice/video infrastructure

**Integrations:**
- **Jane App:** OAuth 2.0 + REST API
- **Stripe:** Payment processing (future)

**Email:**
- **SendGrid:** Transactional emails
- **Alternative:** AWS SES

**Monitoring:**
- **Logs:** CloudWatch Logs
- **Metrics:** CloudWatch Metrics
- **APM:** Sentry (error tracking)
- **Optional:** DataDog (comprehensive monitoring)

**Compliance:**
- **Vanta or Drata:** HIPAA compliance automation
- **Security:** AWS WAF, GuardDuty

### Development Tools

**Version Control:**
- **Git:** GitHub
- **Branching:** GitFlow strategy

**CI/CD:**
- **Platform:** GitHub Actions
- **Deployment:** Automated to staging/production

**Testing:**
- **Python:** pytest, pytest-asyncio, pytest-mock
- **JavaScript:** Jest, React Testing Library, Playwright (E2E)
- **Load Testing:** Locust or k6

**Code Quality:**
- **Python:** Black (formatter), isort, mypy (type checking), ruff (linter)
- **JavaScript:** ESLint, Prettier
- **Pre-commit:** husky + lint-staged

**Infrastructure as Code:**
- **Platform:** Terraform
- **Alternative:** AWS CDK

**Local Development:**
- **Containers:** Docker Compose
- **Tunneling:** ngrok (webhook testing)
- **API Testing:** Postman/Insomnia

---

## System Architecture

### Request Flow: Text Chat

```
1. Patient opens chat widget on practice website
   ↓
2. WebSocket connection to AgentOS API
   ↓
3. Message sent with session_id and customer_id
   ↓
4. API authenticates and routes to Multi-Tenant Agent Manager
   ↓
5. Agent Manager loads/creates Agno agent for customer
   ↓
6. Agno agent:
   - Retrieves session history from PostgreSQL
   - Searches knowledge base (Pinecone) if needed
   - Calls Jane API tools if booking/checking availability
   - Generates response using GPT-4
   ↓
7. Response sent back via WebSocket
   ↓
8. Session saved to PostgreSQL
   ↓
9. Metrics logged to CloudWatch
```

### Request Flow: Voice Call

```
1. Patient calls practice number (forwarded to Twilio)
   ↓
2. Twilio webhook to /voice/incoming/{customer_id}
   ↓
3. API validates customer and creates LiveKit room
   ↓
4. Twilio connects to LiveKit SIP endpoint
   ↓
5. Multi-Tenant Agent Manager spawns voice agent:
   - Loads customer config
   - Initializes Agno agent with voice-optimized settings
   - Wraps Agno agent in LiveKit voice pipeline
   ↓
6. Voice pipeline:
   - STT (Deepgram) transcribes speech
   - Text sent to Agno agent
   - Agent processes (RAG search, Jane API calls)
   - Response generated
   - TTS (ElevenLabs) converts to speech
   - Audio streamed back to caller
   ↓
7. Call transcript and metadata saved
   ↓
8. SMS confirmation sent (if appointment booked)
```

### Cross-Modal Session Continuity

```
Scenario: Patient starts in chat, then calls

1. Patient chats via widget (session_id: abc123)
   - Books appointment partially
   - Decides to call instead
   ↓
2. Widget triggers call with session_id
   ↓
3. Patient calls, provides phone number
   ↓
4. System looks up session by phone or session_id
   ↓
5. Voice agent loads chat history
   ↓
6. Agent continues conversation:
   "Hi! I see you were just asking about appointments for Tuesday.
    Let's finalize that booking over the phone..."
   ↓
7. Both chat and voice transcripts stored under same session
```

---

## Component Design

### 1. Multi-Tenant Agent Manager

**Responsibility:** Create, manage, and route requests to customer-specific Agno agents.

**Key Functions:**
```python
class MultiTenantAgentManager:
    def __init__(self):
        self.agents = {}  # In-memory cache of agent instances
        self.configs = {}  # Customer configurations
    
    async def get_or_create_agent(
        self, 
        customer_id: str, 
        modality: Literal["text", "voice"]
    ) -> Agent:
        """Load or create Agno agent for customer"""
        
    async def route_message(
        self, 
        customer_id: str, 
        session_id: str, 
        message: str
    ) -> AgentResponse:
        """Route message to appropriate agent"""
    
    async def cleanup_idle_agents(self):
        """Remove agents idle for >15 minutes to free memory"""
```

**Caching Strategy:**
- Keep agents in memory for 15 minutes after last use
- LRU eviction if memory pressure
- Agent configs cached in Redis (5 min TTL)

**Isolation:**
- Each agent has customer-specific:
  - System prompt
  - Jane OAuth token
  - Knowledge base namespace
  - Tool permissions

### 2. Knowledge Base Service (RAG)

**Responsibility:** Manage vector embeddings and semantic search for customer knowledge.

**Key Functions:**
```python
class KnowledgeBaseService:
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.namespace = f"clinic_{customer_id}"
        self.pinecone = PineconeClient()
        self.embedder = OpenAIEmbedder()
    
    async def add_document(
        self,
        doc_type: str,
        content: str,
        metadata: dict
    ):
        """Add document to vector store"""
    
    async def search(
        self, 
        query: str, 
        top_k: int = 3,
        filters: dict = None
    ) -> List[Document]:
        """Semantic search for relevant context"""
    
    async def sync_from_jane(self):
        """Sync practitioners, services from Jane API"""
    
    async def process_uploaded_file(self, file: UploadFile):
        """Extract text, chunk, embed, and store"""
```

**Document Processing Pipeline:**
```
Upload → Text Extraction → Chunking → Embedding → Storage
          (PyPDF2, docx)   (500 words)  (OpenAI)   (Pinecone)
```

**Chunking Strategy:**
- 500 tokens per chunk
- 50 token overlap
- Respect sentence boundaries
- Metadata: source, chunk_index, doc_type

### 3. Jane App Integration Service

**Responsibility:** Handle all communication with Jane App API.

**Key Functions:**
```python
class JaneAPIClient:
    def __init__(self, oauth_token: str):
        self.token = oauth_token
        self.base_url = "https://api.jane.app/v1"
        self.session = aiohttp.ClientSession()
    
    async def get_availability(
        self, 
        date: str, 
        practitioner_id: Optional[str] = None
    ) -> List[TimeSlot]:
        """Get available appointment slots"""
    
    async def create_appointment(
        self,
        patient_id: str,
        datetime: str,
        service_id: str,
        practitioner_id: str
    ) -> Appointment:
        """Book appointment"""
    
    async def find_or_create_patient(
        self,
        name: str,
        phone: str,
        email: Optional[str] = None
    ) -> Patient:
        """Look up patient or create new record"""
    
    async def get_invoice_status(
        self, 
        invoice_id: str
    ) -> Invoice:
        """Check payment status"""
```

**Error Handling:**
- Retry with exponential backoff (3 attempts)
- Circuit breaker pattern (5 failures = 30s cooldown)
- Graceful degradation (cache last known availability)

**Rate Limiting:**
- Respect Jane's limits (likely 100 req/min)
- Token bucket algorithm
- Per-customer rate tracking

**Caching:**
- Availability: 5-minute TTL
- Practitioner/service data: 1-hour TTL
- Invalidate on webhook updates

### 4. Voice Pipeline Adapter

**Responsibility:** Bridge Agno agents to LiveKit voice pipeline.

**Architecture:**
```python
class VoicePipelineAdapter:
    def __init__(self, agno_agent: Agent, customer_config: dict):
        self.agno_agent = agno_agent
        self.config = customer_config
        self.session_id = str(uuid.uuid4())
    
    async def create_voice_agent(self) -> VoicePipelineAgent:
        """Create LiveKit agent that uses Agno for logic"""
        return VoicePipelineAgent(
            vad=SileroVAD(),
            stt=DeepgramSTT(model="nova-2"),
            llm=AgnoLLMWrapper(self.agno_agent, self.session_id),
            tts=ElevenLabsTTS(voice_id=self.config.voice_id)
        )
    
class AgnoLLMWrapper:
    """Wrapper to use Agno agent as LLM in LiveKit"""
    async def chat(self, messages: List[dict]) -> dict:
        # Convert LiveKit format to Agno format
        # Run Agno agent
        # Return response
```

**Voice Optimization:**
- Disable markdown formatting
- Shorter responses (prefer 2-3 sentences)
- Natural filler words ("um", "let me check")
- Interrupt handling

### 5. Session Manager

**Responsibility:** Manage conversation sessions across modalities.

**Data Model:**
```python
@dataclass
class Session:
    id: str  # UUID
    customer_id: str
    user_id: Optional[str]  # Patient identifier
    modality: Literal["text", "voice"]
    started_at: datetime
    last_activity: datetime
    messages: List[Message]
    context: dict  # Shared state
    metadata: dict  # call_sid, phone_number, etc.

@dataclass
class Message:
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    modality: Literal["text", "voice"]
    metadata: dict
```

**Key Functions:**
```python
class SessionManager:
    async def create_session(
        self, 
        customer_id: str, 
        modality: str
    ) -> Session:
        """Create new session"""
    
    async def get_session(self, session_id: str) -> Session:
        """Retrieve session with history"""
    
    async def add_message(
        self, 
        session_id: str, 
        message: Message
    ):
        """Append message to session"""
    
    async def switch_modality(
        self, 
        session_id: str, 
        new_modality: str
    ):
        """Handle modality switch (chat → voice)"""
```

**Storage:**
- Active sessions: Redis (fast access)
- Completed sessions: PostgreSQL (long-term)
- Auto-expire Redis after 1 hour idle
- Flush to PostgreSQL on completion

### 6. Twilio Integration Service

**Responsibility:** Handle phone number provisioning, call routing, and SMS.

**Key Functions:**
```python
class TwilioService:
    def __init__(self):
        self.client = TwilioClient(account_sid, auth_token)
    
    async def provision_number(
        self, 
        customer_id: str, 
        area_code: str
    ) -> str:
        """Buy phone number for customer"""
    
    async def configure_webhooks(
        self, 
        phone_number: str, 
        customer_id: str
    ):
        """Set up call/SMS webhooks"""
    
    async def send_sms(
        self, 
        to: str, 
        body: str, 
        from_: str
    ):
        """Send SMS confirmation"""
    
    async def initiate_call(
        self, 
        to: str, 
        from_: str, 
        session_id: str
    ):
        """Trigger outbound call (for "call me" feature)"""
```

---

## Data Architecture

### Database Schema

**PostgreSQL Tables (Shared Database)**

**Tables from Next.js SaaS Starter (Pre-existing):**

```sql
-- User Management (from SaaS Starter)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Team Management (from SaaS Starter)
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member', -- 'owner' or 'member'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subscriptions (from SaaS Starter)
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    plan_name VARCHAR(50), -- 'starter', 'professional', 'enterprise'
    status VARCHAR(50), -- 'active', 'canceled', 'past_due'
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Activity Logs (from SaaS Starter)
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    action VARCHAR(255) NOT NULL,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Custom Tables for Jane Agent (Added by us):**

```sql
-- Customer practice settings (links to team from SaaS Starter)
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    practice_name VARCHAR(255) NOT NULL,
    jane_oauth_token TEXT,  -- Encrypted
    twilio_phone_number VARCHAR(20),
    plan_tier VARCHAR(50) DEFAULT 'starter',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'
);

-- Agent configurations
CREATE TABLE agent_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    system_prompt TEXT NOT NULL,
    enabled_features JSONB DEFAULT '[]',
    voice_settings JSONB DEFAULT '{}',
    business_hours JSONB,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Practitioners
CREATE TABLE practitioners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    jane_id VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(100),
    specialty VARCHAR(100),
    bio TEXT,
    schedule_info JSONB,
    custom_settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge base documents
CREATE TABLE knowledge_docs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    doc_type VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    vector_id VARCHAR(255),  -- Pinecone ID
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sessions (for agent conversations)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    user_id VARCHAR(100),  -- Patient phone/email
    modality VARCHAR(20) NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    last_activity TIMESTAMP DEFAULT NOW(),
    context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    modality VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Call logs
CREATE TABLE call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id),
    call_sid VARCHAR(100),
    from_number VARCHAR(20),
    to_number VARCHAR(20),
    duration INTEGER,  -- seconds
    outcome VARCHAR(50),  -- booked, inquiry, error, etc.
    transcript_summary TEXT,
    cost_cents INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- PHI access logs (HIPAA requirement)
CREATE TABLE phi_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    action VARCHAR(100) NOT NULL,
    data_accessed JSONB NOT NULL,
    user_agent VARCHAR(255),
    ip_address INET,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Usage tracking
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    text_messages INTEGER DEFAULT 0,
    voice_minutes INTEGER DEFAULT 0,
    cost_cents INTEGER DEFAULT 0,
    UNIQUE(customer_id, date)
);
```

**Database Ownership:**
- **Next.js manages:** users, teams, team_members, subscriptions, activity_logs
- **FastAPI manages:** customers, agent_configs, practitioners, knowledge_docs, sessions, messages, call_logs, phi_access_logs, usage_logs
- **Relationship:** customers.team_id → teams.id (links both systems)

**Indexes:**
```sql
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_sessions_customer_id ON sessions(customer_id);
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_call_logs_customer_id ON call_logs(customer_id);
CREATE INDEX idx_call_logs_timestamp ON call_logs(timestamp);
CREATE INDEX idx_phi_logs_customer_id ON phi_access_logs(customer_id);
CREATE INDEX idx_usage_customer_date ON usage_logs(customer_id, date);
```

### Redis Data Structures

**Session Cache:**
```
Key: session:{session_id}
Type: Hash
TTL: 1 hour
Fields:
  customer_id
  user_id
  modality
  context (JSON)
  last_activity
```

**Rate Limiting:**
```
Key: rate_limit:{customer_id}:{endpoint}
Type: String (counter)
TTL: 1 minute
```

**Jane API Cache:**
```
Key: jane_availability:{customer_id}:{date}
Type: String (JSON)
TTL: 5 minutes

Key: jane_services:{customer_id}
Type: String (JSON)
TTL: 1 hour
```

**Agent Instance Cache:**
```
Key: agent_config:{customer_id}
Type: String (JSON)
TTL: 5 minutes
```

### Pinecone Vector Index

**Index Configuration:**
```
Name: clinic-knowledge
Dimension: 1536 (text-embedding-3-small)
Metric: cosine
Pods: Serverless (auto-scaling)
```

**Namespace Structure:**
```
clinic_{customer_id}  # One namespace per customer
```

**Vector Metadata:**
```json
{
  "customer_id": "uuid",
  "doc_type": "practitioner|service|faq|policy|uploaded_doc",
  "content": "full text chunk",
  "source": "jane_api|user_input|uploaded_file",
  "practitioner_id": "optional",
  "timestamp": "iso8601",
  "chunk_index": 0,
  "total_chunks": 5
}
```

---

## API Design

### REST API Endpoints

**Base URL:** `https://api.yourapp.com/v1`

#### Authentication Endpoints

```
POST   /auth/signup
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
GET    /auth/me
```

#### Customer Management

```
GET    /customers/me
PATCH  /customers/me
DELETE /customers/me
POST   /customers/jane/connect      # OAuth flow
GET    /customers/jane/status
```

#### Agent Configuration

```
GET    /agents/config
PUT    /agents/config
GET    /agents/test                  # Test agent in playground
```

#### Knowledge Base

```
GET    /knowledge
POST   /knowledge/documents          # Upload file
DELETE /knowledge/documents/:id
POST   /knowledge/sync-jane          # Manual sync
GET    /knowledge/search             # Test RAG search
```

#### Chat (Text)

```
POST   /chat/sessions                # Create session
GET    /chat/sessions/:id
POST   /chat/sessions/:id/messages   # Send message
DELETE /chat/sessions/:id            # End session
```

**WebSocket:**
```
WS     /chat/ws/:session_id          # Real-time chat
```

#### Voice

```
POST   /voice/incoming/:customer_id  # Twilio webhook
POST   /voice/status/:customer_id    # Call status callback
POST   /voice/initiate               # Trigger outbound call
```

#### Analytics

```
GET    /analytics/overview
GET    /analytics/calls
GET    /analytics/usage
GET    /analytics/export
```

#### Billing

```
GET    /billing/usage
GET    /billing/invoices
POST   /billing/upgrade
POST   /billing/payment-method
```

### API Response Format

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2025-11-22T10:00:00Z"
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Customer not found",
    "details": { ... }
  },
  "timestamp": "2025-11-22T10:00:00Z"
}
```

### WebSocket Protocol (Chat)

**Client → Server:**
```json
{
  "type": "message",
  "content": "I need to book an appointment",
  "session_id": "uuid",
  "metadata": { ... }
}
```

**Server → Client:**
```json
{
  "type": "message",
  "content": "I'd be happy to help you book...",
  "timestamp": "2025-11-22T10:00:00Z",
  "metadata": {
    "agent_name": "Practice Assistant",
    "confidence": 0.95
  }
}
```

**Typing Indicator:**
```json
{
  "type": "typing",
  "is_typing": true
}
```

---

## Security Architecture

### Authentication & Authorization

**JWT Token Structure:**
```json
{
  "sub": "customer_id",
  "email": "user@practice.com",
  "role": "admin",
  "permissions": ["manage_agent", "view_analytics"],
  "exp": 1700000000,
  "iat": 1700000000
}
```

**Token Types:**
- **Access Token:** Short-lived (15 min), for API requests
- **Refresh Token:** Long-lived (7 days), to get new access tokens
- **Session Token:** For WebSocket connections

**OAuth 2.0 Flow (Jane App):**
```
1. User clicks "Connect Jane"
2. Redirect to Jane OAuth page
3. User approves
4. Jane redirects with code
5. Exchange code for access/refresh tokens
6. Store encrypted tokens in database
```

### Data Encryption

**At Rest:**
- Database: AWS RDS encryption (AES-256)
- S3: Server-side encryption (SSE-S3)
- Sensitive fields: Application-level encryption (Fernet)
  - Jane OAuth tokens
  - API keys
  - Patient PHI

**In Transit:**
- TLS 1.3 for all connections
- Certificate pinning for mobile apps
- HTTPS only (HSTS enabled)

**Key Management:**
- AWS KMS for encryption keys
- Automatic key rotation (90 days)
- Separate keys per environment

### HIPAA Compliance

**Technical Safeguards:**
```python
# Audit logging middleware
@app.middleware("http")
async def audit_phi_access(request: Request, call_next):
    if is_phi_endpoint(request.url):
        log_phi_access(
            customer_id=request.state.customer_id,
            action=f"{request.method} {request.url}",
            data_accessed=extract_phi_fields(request),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
    return await call_next(request)
```

**Access Controls:**
- Role-based access (admin, staff, readonly)
- MFA required for admin actions
- IP whitelisting available
- Session timeout (15 minutes idle)

**Data Retention:**
- Call recordings: 30-90 days (configurable)
- Chat logs: 1 year
- Audit logs: 6 years (HIPAA requirement)
- Automatic purge jobs

**Breach Notification:**
- Automated detection of suspicious access
- Incident response playbook
- Customer notification within 24 hours
- HHS reporting within 60 days

### Rate Limiting

**Strategy:** Token bucket per customer

```python
RATE_LIMITS = {
    "starter": {
        "api_requests": "100/minute",
        "chat_messages": "50/minute",
        "voice_calls": "10/minute"
    },
    "professional": {
        "api_requests": "200/minute",
        "chat_messages": "100/minute",
        "voice_calls": "20/minute"
    },
    "enterprise": {
        "api_requests": "500/minute",
        "chat_messages": "200/minute",
        "voice_calls": "50/minute"
    }
}
```

### Input Validation

**Request Validation:**
- Pydantic models for all endpoints
- SQL injection prevention (parameterized queries)
- XSS protection (sanitize user input)
- CSRF tokens for state-changing operations

**Agent Input Sanitization:**
- Strip PII from logs
- Redact sensitive info in transcripts
- Validate all tool parameters

---

## Deployment Architecture

### Environments

**Development:**
- Next.js: Local development server (`pnpm dev`)
- FastAPI: Local with Docker Compose
- Shared local PostgreSQL
- Mock external services

**Staging:**
- Next.js: Vercel preview deployment
- FastAPI: AWS staging environment
- Shared RDS database (staging)
- Seeded with test data

**Production:**
- Next.js: Vercel production
- FastAPI: AWS production (multi-AZ)
- Shared RDS database (production)
- Comprehensive monitoring

### Deployment Strategy

**Next.js Frontend (SaaS Starter):**
```
GitHub → Vercel (Automatic Deployment)
- Push to 'main' → Production
- Pull requests → Preview deployments
- Environment variables in Vercel dashboard
- Edge functions for API routes
```

**FastAPI Backend (Agent Engine):**
```
GitHub → GitHub Actions → AWS ECS
- Push to 'develop' → Staging
- Push to 'main' → Production
- Docker build and push to ECR
- ECS service update
```

### AWS Infrastructure

```
┌─────────────────────────────────────────────────┐
│               Production VPC                    │
│                                                 │
│  ┌──────────────┐         ┌──────────────┐     │
│  │ Public Subnet│         │Public Subnet │     │
│  │   (AZ-1)     │         │   (AZ-2)     │     │
│  │              │         │              │     │
│  │  ALB         │         │  ALB         │     │
│  │  NAT Gateway │         │  NAT Gateway │     │
│  └──────────────┘         └──────────────┘     │
│         │                        │             │
│  ┌──────────────┐         ┌──────────────┐     │
│  │Private Subnet│         │Private Subnet│     │
│  │   (AZ-1)     │         │   (AZ-2)     │     │
│  │              │         │              │     │
│  │  ECS Tasks   │         │  ECS Tasks   │     │
│  │  (API/Agent) │         │  (API/Agent) │     │
│  └──────────────┘         └──────────────┘     │
│         │                        │             │
│  ┌──────────────┐         ┌──────────────┐     │
│  │Private Subnet│         │Private Subnet│     │
│  │   (AZ-1)     │         │   (AZ-2)     │     │
│  │              │         │              │     │
│  │  RDS Primary │         │  RDS Replica │     │
│  │  ElastiCache │         │  ElastiCache │     │
│  └──────────────┘         └──────────────┘     │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Components:**
- **CloudFront:** CDN for frontend assets
- **ALB:** Load balancing, SSL termination
- **ECS Fargate:** Containerized API/agents
- **RDS PostgreSQL:** Multi-AZ, automated backups
- **ElastiCache Redis:** Multi-AZ replication
- **S3:** Document storage, backups
- **Secrets Manager:** Credentials
- **CloudWatch:** Logs and metrics

### Container Architecture

**Dockerfile (API):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run as non-root user
RUN useradd -m appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose (Local Dev):**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/appdb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./:/app
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=appdb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    volumes:
      - redis_data:/data
  
  celery:
    build: .
    command: celery -A tasks worker --loglevel=info
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
```

### CI/CD Pipeline

**GitHub Actions Workflow:**

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t app:${{ github.sha }} .
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker tag app:${{ github.sha }} $ECR_REGISTRY/app:${{ github.sha }}
          docker push $ECR_REGISTRY/app:${{ github.sha }}
  
  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to ECS Staging
        run: |
          aws ecs update-service --cluster staging --service api --force-new-deployment
  
  deploy-production:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to ECS Production
        run: |
          aws ecs update-service --cluster production --service api --force-new-deployment
```

---

## Scalability & Performance

### Horizontal Scaling Strategy

**API Layer:**
- Auto-scaling ECS tasks (2-20 instances)
- Scale trigger: CPU >70% or request count >1000/min
- Stateless design (sessions in Redis/DB)

**Agent Layer:**
- Dynamic agent instantiation
- In-memory caching with LRU eviction
- Connection pooling for DB/Redis

**Database:**
- Read replicas for analytics queries
- Connection pooling (PgBouncer)
- Query optimization and indexing

**Voice Pipeline:**
- LiveKit cloud auto-scaling
- Multiple LiveKit nodes for redundancy

### Caching Strategy

**Multi-Layer Cache:**
```
Request → API Cache (Redis) → Agent Cache (Memory) → Database
          5 min TTL              15 min TTL
```

**Cache Keys:**
- Customer config: `config:{customer_id}`
- Jane availability: `jane_avail:{customer_id}:{date}`
- Knowledge search: `kb_search:{customer_id}:{query_hash}`

**Cache Invalidation:**
- Time-based expiry
- Event-driven (webhook from Jane)
- Manual purge via admin API

### Performance Optimization

**Database:**
- Prepared statements
- Index optimization
- Partition large tables (call_logs by month)
- EXPLAIN ANALYZE for slow queries

**API:**
- Async/await throughout
- Connection pooling
- Batch operations where possible
- Gzip compression

**Agent:**
- Parallel tool calls
- Streaming responses
- Early stopping for long responses
- Model selection (fast vs. accurate)

### Load Testing

**Tools:** Locust or k6

**Test Scenarios:**
- Baseline: 100 concurrent users
- Peak: 1000 concurrent users
- Spike: 0 → 500 users in 1 minute
- Endurance: 200 users for 2 hours

**Targets:**
- API: <200ms p95 latency
- Chat: <2s response time
- Voice: <500ms latency
- Database: <100ms query time

---

## Monitoring & Observability

### Metrics

**System Metrics:**
- CPU, memory, disk usage
- Network I/O
- Container health
- Database connections

**Application Metrics:**
- Request rate, latency, errors
- Agent initialization time
- RAG search latency
- Jane API response time
- Voice pipeline latency

**Business Metrics:**
- Active customers
- Calls/chats per day
- Booking success rate
- Revenue (MRR, churn)

### Logging

**Structured Logging:**
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "agent_message_processed",
    customer_id=customer_id,
    session_id=session_id,
    duration_ms=duration,
    tools_called=["check_availability"],
    outcome="booking_successful"
)
```

**Log Levels:**
- ERROR: Failures requiring attention
- WARN: Degraded performance, retries
- INFO: Normal operations
- DEBUG: Detailed troubleshooting (dev only)

**Log Aggregation:**
- CloudWatch Logs (centralized)
- Log groups per service
- Retention: 30 days (reduce costs)
- Export critical logs to S3 (long-term)

### Alerting

**Critical Alerts (PagerDuty):**
- Service down (health check fails)
- Error rate >5%
- Database connection pool exhausted
- HIPAA breach detected

**Warning Alerts (Slack):**
- Latency p95 >500ms
- Failed Jane API calls >10/min
- High memory usage >80%
- Unusual traffic patterns

**Business Alerts (Email):**
- New customer signup
- Customer churned
- Usage limit reached
- Monthly revenue report

### Dashboards

**CloudWatch Dashboard:**
- API request volume
- Error rates
- Latency (p50, p95, p99)
- Database performance
- Cost tracking

**Custom Dashboard (Grafana optional):**
- Customer health scores
- Agent performance by customer
- Booking conversion funnel
- Revenue trends

### Distributed Tracing

**OpenTelemetry Integration:**
- Trace requests across services
- Visualize call paths
- Identify bottlenecks
- Debug cross-service issues

**Example Trace:**
```
/chat/message
  ├─ get_session (5ms)
  ├─ load_agent (120ms)
  │   ├─ load_config (10ms)
  │   ├─ search_knowledge (80ms)
  │   └─ init_tools (30ms)
  ├─ agent.run (850ms)
  │   ├─ llm_call (600ms)
  │   └─ jane_api.check_availability (250ms)
  └─ save_message (15ms)
Total: 990ms
```

---

## Disaster Recovery

### Backup Strategy

**Database (PostgreSQL):**
- Automated daily backups (AWS RDS)
- Point-in-time recovery (PITR) enabled
- Backup retention: 30 days
- Cross-region replication for critical data

**Object Storage (S3):**
- Versioning enabled
- Lifecycle policy: Archive to Glacier after 90 days
- Cross-region replication for documents

**Configuration:**
- Infrastructure as Code (Terraform state in S3)
- Secrets backed up to secure offline storage
- Code in Git (GitHub, GitLab)

### Recovery Procedures

**Recovery Time Objective (RTO):** 4 hours  
**Recovery Point Objective (RPO):** 1 hour

**Scenario 1: Database Failure**
1. Promote read replica to primary (5-10 min)
2. Update connection strings
3. Verify data integrity
4. Resume operations

**Scenario 2: Complete Region Failure**
1. Activate disaster recovery plan
2. Restore database from backup in alternate region
3. Deploy application to alternate region
4. Update DNS to point to new region
5. Estimated downtime: 2-4 hours

**Scenario 3: Data Corruption**
1. Identify corruption scope
2. Restore from PITR backup
3. Replay transactions from transaction log
4. Validate data integrity

### Business Continuity

**Communication Plan:**
- Status page (e.g., status.yourapp.com)
- Email notifications to customers
- Slack/webhook for internal team
- Regular updates during incident

**Failover Testing:**
- Quarterly DR drills
- Test backup restoration
- Validate failover procedures
- Update runbooks based on learnings

---

## Open Technical Questions

1. **LiveKit HIPAA Compliance:** Confirm BAA availability or plan self-hosted
2. **Pinecone vs. pgvector:** Evaluate cost at scale (>1000 customers)
3. **Jane API Rate Limits:** Get official documentation from Jane
4. **Real-time Agent Updates:** How to push config changes to running agents?
5. **Voice Quality Metrics:** How to measure and ensure consistent quality?
6. **Multi-Region:** When to expand beyond us-east-1?
7. **Agent Versioning:** How to A/B test agent improvements?
8. **Cost Optimization:** Reserved instances vs. spot for savings?

---

## Appendix

### Technology Evaluation Matrix

| Category | Option 1 | Option 2 | Winner | Reason |
|----------|----------|----------|--------|--------|
| Agent Framework | Agno | LangGraph | **Agno** | Voice + text support, faster |
| Vector DB | Pinecone | pgvector | **Pinecone** | Managed, easier to start |
| Voice STT | Deepgram | AssemblyAI | **Deepgram** | Lower latency |
| Voice TTS | ElevenLabs | Cartesia | **ElevenLabs** | Better quality |
| Hosting | AWS | GCP | **AWS** | Team familiarity, HIPAA |

### Glossary

- **Agno:** Multi-agent framework for building AI agents
- **AgentOS:** Agno's production runtime (FastAPI app)
- **LiveKit:** Real-time voice/video infrastructure
- **RAG:** Retrieval-Augmented Generation
- **STT:** Speech-to-Text
- **TTS:** Text-to-Speech
- **VAD:** Voice Activity Detection
- **ECS:** AWS Elastic Container Service
- **RDS:** AWS Relational Database Service

---

**Document Status:** Draft v1.0  
**Next Review:** After initial implementation  
**Feedback:** email@yourapp.com
