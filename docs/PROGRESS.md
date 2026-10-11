
# ReturnGuard Progress

## Current milestone

Phase 0 — Foundation

## Target architecture

See [ARCHITECTURE.md](ARCHITECTURE.md).

## Completed

- [ ] Verify Git, Python, Node.js, npm and VS Code.
- [ ] Create the repository and initial Git commit.
- [ ] Create Python virtual environment.
- [ ] Install FastAPI and test dependencies.
- [ ] Implement GET /health.
- [ ] Pass the health endpoint test.
- [ ] Generate the Next.js frontend.
- [ ] Install Docker Desktop.
- [ ] Verify local development environment.

## Current state

No services beyond the initial API are considered implemented
until their tests pass.

## Next milestone

Phase 1 — Dataset, refund domain model, and deterministic
refund eligibility engine.

## Known limitations

- No database connection yet.
- No authentication yet.
- No refund processing or payment integration.
- No LLM or ML model yet.
- No queue or background worker yet.

## Decisions to preserve

- PostgreSQL is the source of truth.
- Redis is for transient coordination and jobs.
- LLM output is not authorization.
- Every final decision must be auditable.
- Human approval is required for configured denials and
  high-risk outcomes.
