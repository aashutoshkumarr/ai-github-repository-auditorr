# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]
- Convert job queue to Postgres-backed async SQLAlchemy store with Alembic migrations.
- Durable job queue tables: audit_jobs, pending_jobs with visibility/lock fields.
- Safe multi-worker dequeue using SELECT FOR UPDATE SKIP LOCKED with SQLite fallback.
- Visibility timeout and automatic reclaim of stuck jobs.
- Sandbox runner: run analysis inside disposable Docker containers for tenant isolation.
- Worker integrates sandbox mode (SANDBOX_ENABLED) and reclaimer loop.
- Prometheus metrics for job lifecycle and reclamation.
- Docker Compose production example with migrate one-shot service.
- Alembic scaffolding and migration scripts (0001..0004).
- CI workflow to run tests and build images (GitHub Actions).

## Notes
- See backend/README or RELEASE_NOTES.md for deployment and operational instructions.
