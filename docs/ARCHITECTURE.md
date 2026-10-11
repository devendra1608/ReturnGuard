
# ReturnGuard — Canonical Architecture

## Goal

Build a governed AI-powered e-commerce return/refund review
system. The application evaluates requests, collects evidence,
applies deterministic policies, and routes uncertain or risky
cases to authorized human reviewers.

## Layer 1 — Client

Roles:
- Customer
- Reviewer
- Administrator

Responsibilities:
- Submit returns and evidence.
- Track return status.
- Review evidence and explanations.
- Perform authorized review actions.

## Layer 2 — Frontend and Identity

Frontend:
- Next.js App Router
- TypeScript
- Customer, reviewer, and admin interfaces
- Auth.js server-side token proxy

Identity:
- Keycloak
- OpenID Connect (OIDC)
- Authorization Code Flow with PKCE
- Role and session management

Browser authentication credentials must not expose
backend access tokens to client-side JavaScript.

## Layer 3 — API Backend

- Python 3.13
- FastAPI
- Pydantic
- SQLAlchemy 2 async
- PostgreSQL
- WebSocket endpoint: /ws/returns

Responsibilities:
- Authenticate and authorize requests.
- Validate inputs.
- Persist return cases and audit events.
- Queue workflow jobs.
- Expose case and review APIs.
- Publish real-time status updates.

## Layer 4 — Background Worker and Agent Pipeline

- Redis
- ARQ worker
- LangGraph
- PostgreSQL-backed workflow checkpointing

Target workflow:
1. Data Quality Gate
2. Planner
3. Intake
4. Policy (RAG)
5. Image
6. Behavior
7. Decision
8. Critic
9. Explanation
10. Governance Gate

Agent outputs are evidence and proposals, not authorization
to execute financial actions.

Configured denials and other high-risk outcomes require
human review before the final action.

## Layer 5 — AI and Governance Infrastructure

- Bifrost: LLM gateway, routing, limits, fallbacks
- Optional paid providers: Groq API and OpenAI API
- IBM ContextForge: MCP governance gateway
- MCP Tools Server: approved tools only
- OPA: deterministic tool/model authorization policies
- Qdrant: policy vector retrieval
- Local CPU ML: scikit-learn risk model and image signals

Policy enforcement must fail closed when authorization
cannot be established.

## Layer 6 — Observability

- Langfuse v3: traces and versioned prompts
- Prometheus: metrics
- Grafana: dashboards and alerts

Record model and prompt versions, policy versions,
case identifiers, timings, token usage, and estimated cost
where available.

Never log secrets or unnecessary sensitive customer data.

## Layer 7 — Local Infrastructure

- PostgreSQL: cases, decisions, users and audit records
- Redis: queue, cache and pub/sub
- MinIO: return photos and evidence
- MailHog: local email testing
- HashiCorp Vault: secrets
- Docker Compose: local orchestration

PostgreSQL is the source of truth for business state.
Redis is not the permanent audit store.

## Return Processing Flow

1. Customer submits a request.
2. API authenticates, validates, and stores the case.
3. API queues an asynchronous job.
4. ARQ runs the LangGraph workflow.
5. Agents collect structured evidence and assessments.
6. OPA and deterministic business rules constrain actions.
7. Governance gate approves, escalates, or pauses the case.
8. Authorized decisions and audit events are persisted.
9. Dashboard receives status updates.
10. Reviewer actions are authenticated, authorized, and audited.

## Core Safety Invariants

- No refund action without explicit server-side authorization.
- Duplicate job execution must not create duplicate refunds.
- Human approval must be persisted and tied to an authorized actor.
- Model failure must not bypass policy enforcement.
- Policy decisions and final outcomes must be auditable.
- Workflow state must be recoverable after failures.

## Development Strategy

Implement incrementally:
1. Repository and API foundation.
2. Data model and deterministic policy engine.
3. PostgreSQL persistence.
4. Risk model and evaluation.
5. LangGraph workflow.
6. Redis and ARQ.
7. Authentication and governance.
8. RAG and image evidence.
9. Frontend and reviewer workflow.
10. Observability, integration testing, and release.

The architecture is the target design. Components are not
considered implemented until integrated and tested.
