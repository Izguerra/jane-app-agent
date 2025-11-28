# Coding Standards & Guidelines

This document outlines the development standards, architectural principles, and best practices for the Jane AI Agent project. All contributions must adhere to these guidelines to ensure maintainability, scalability, and code quality.

## 1. Software Development Life Cycle (SDLC)
*   **Planning:** Every feature or refactor must start with a clear plan or design document.
*   **Version Control:** Use meaningful commit messages. Feature branches should be used for new development.
*   **Testing:** All new features must include verification steps (automated tests where possible, or detailed manual verification plans).
*   **Review:** Code must be reviewed (self-review or peer-review) before merging.
*   **Documentation:** Update documentation (README, API docs, inline comments) as code evolves.

## 2. Architecture & Database Design
*   **Separation of Concerns:** Maintain strict boundaries between layers (Frontend, API, Service, Data Access).
*   **Scalability:** Design systems to handle growth. Use asynchronous processing for heavy tasks (e.g., Celery/Redis).
*   **Database Normalization:** Follow standard normalization rules (3NF) unless performance dictates otherwise.
*   **Migrations:** All database changes must be managed via migration scripts (Alembic/Drizzle).
*   **Security:** Never commit secrets. Use environment variables. Validate all inputs.
*   **⚠️ CRITICAL: Never modify the `.env` file programmatically.** All environment variable changes must be requested from the user. The AI assistant must never read, write, or modify `.env` files.

## 3. Modularity & Reusability
*   **No Monoliths:** Break down large files and functions into smaller, single-purpose units.
*   **Reusable Components:**
    *   **Frontend:** Extract common UI patterns into reusable React components (e.g., `components/ui/`). Avoid hardcoding styles; use Tailwind utility classes.
    *   **Backend:** Use Services and Routers to organize logic. Do not put business logic inside route handlers.
*   **DRY (Don't Repeat Yourself):** Abstract repeated logic into utility functions or shared libraries.

## 4. Production-First Development

**CRITICAL RULE: All code must be production-ready from day one. No mock data, demo content, or placeholder implementations are allowed.**

### Prohibited Practices
*   ❌ Mock API responses or tokens
*   ❌ Demo data or sample content  
*   ❌ Placeholder keys or credentials
*   ❌ Fallback to fake/mock services
*   ❌ "TODO" implementations that return dummy data
*   ❌ Development-only code paths that bypass real functionality
*   ❌ Default values for service credentials

### Required Practices
*   ✅ Proper error handling with meaningful messages
*   ✅ HTTP error codes (503 for service unavailable, 500 for server errors)
*   ✅ Environment variable validation at startup or first use
*   ✅ Clear error messages indicating missing configuration
*   ✅ Graceful degradation with user-facing explanations
*   ✅ Fail fast when required services are not configured

### Example: API Token Generation

**❌ Wrong:**
```python
if not api_key:
    return {"token": "mock_token", "url": "wss://mock.example.com"}
```

**✅ Correct:**
```python
if not api_key:
    raise HTTPException(
        status_code=503,
        detail="LiveKit is not configured. Missing: LIVEKIT_API_KEY"
    )
```

## 5. Code Style
*   **Frontend:** Follow Next.js and React best practices. Use TypeScript for type safety.
*   **Backend:** Follow PEP 8 for Python code. Use Pydantic for data validation.
