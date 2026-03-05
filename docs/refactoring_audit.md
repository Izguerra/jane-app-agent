# Project Codebase Audit & Refactoring Plan

## Executive Summary
The project contains several monolithic files (>500 lines) that mix concerns (DB access, business logic, external API calls). Following a Service-Oriented Architecture (SOA) pattern within the monolith is recommended to improve scalability, testability, and security.

## 1. High-Priority Refactoring Targets

### A. `backend/agent_tools.py` (843 lines)
**Current State**: Contains all tool definitions (Appointments, Weather, Knowledge Base, Customer Auth).
**Problem**: Hard to maintain; testing one tool requires loading dependencies for all.
**Proposed Refactor**:
- Create package `backend/tools/`.
- Split into:
    - `appointment_tools.py` (Create/Edit/Cancel, Availability)
    - `customer_tools.py` (Register, Identity Check)
    - `context_tools.py` (Weather, Time)
    - `knowledge_tools.py` (RAG search)
- `AgentTools` becomes a facade or registry.

### B. `backend/voice_agent.py` (717 lines)
**Current State**: Handles server startup, VAD prewarming, Context creation, Prompt engineering, and Event loop.
**Problem**: "God object" for the voice agent. Prompt logic is hardcoded.
**Proposed Refactor**:
- Extract prompt logic to `backend/services/prompt_service.py`.
- Extract context/session setup to `backend/services/session_service.py`.

### C. Backend Routers (`workspaces.py`, `admin_settings.py`)
**Current State**: Routers contain direct SQL queries, Stripe API calls, and raw data aggregation.
**Problem**: Violates separation of concerns; logic is not reusable.
**Proposed Refactor**:
- **Service Layer**: Ensure strictly `Router -> Service -> DB`.
    - `WorkspaceService`: Handle aggregation of stats.
    - `BillingService`: Handle Stripe logic (invoice fetching, LTV calc).
    - `AdminService`: Handle global settings.

## 2. Architecture & Design Reviews

### Service Layer Pattern
**Observation**: logic is leaking into Routers (`routers/workspaces.py`).
**Recommendation**:
- Enforce that Routes ONLY handle request parsing and response formatting.
- All business logic (e.g., "Calculate MRR", "Fetch Stripe Invoices") belongs in `backend/services/`.

### Security & Privacy (RBAC)
**Observation**: RBAC is checked manually in some routes (`if user.role not in [...]`).
**Recommendation**:
- Standardize on a `require_role(["admin", "owner"])` dependency or middleware to prevent accidental omission.
- Ensure all queries are scoped by `workspace_id` (Multi-tenancy enforcement).

### Database Schema
**Observation**: `models_db.py` is growing (563 lines).
**Recommendation**:
- Split models into logical modules if it grows >1000 lines (e.g., `models/crm.py`, `models/core.py`).
- Ensure all new tables have `workspace_id` and proper indexes (like the `confirmation_code` update).

## 3. Frontend Architecture
**Observation**: Large page components (e.g., `admin/workspaces/page.tsx`, `sidebar.tsx`).
**Recommendation**:
- **Atomic Design**: Move reusable chunks (tables, dialogs) to `components/`.
- **Data Fetching**: Continue using SWR, but move fetchers and keys to a typed `hooks/useWorkspaces.ts` etc. to interact with the API typesafely.

## 4. Proposed Folder Structure (Backend)
## 5. Security & Scalability Findings

### Scalability: SSE Implementation
**Observation**: `backend/routers/agents.py` uses a global in-memory set `settings_listeners` for Server-Sent Events.
**Problem**: This works only for a single server instance. If scaled to multiple workers or nodes, events will not broadcast correctly.
**Recommendation**: Use **Redis Pub/Sub** to handle text-based event broadcasting across instances.

### Security: PII & Logging
**Observation**: `backend/auth.py` logs partial tokens on error.
**Recommendation**: Remove token logging or hash tokens before logging for debugging.
**Observation**: `backend/voice_agent.py` handles transcripts locally.
**Recommendation**: Ensure `RECORDINGS_DIR` is mounted on ephemeral storage or strictly access-controlled in production. Ensure transcripts are redacted before logging to standard output.

### Privacy: Tenant Isolation
**Observation**: Most services rely on manual `workspace_id` filtering.
**Recommendation**: Create a `ScopedSession` or repository pattern that *automatically* applies `filter(workspace_id=...)` base query to prevent accidental data leaks.

