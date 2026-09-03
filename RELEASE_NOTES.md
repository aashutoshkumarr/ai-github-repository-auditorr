AI GitHub Repository Auditor — Release Notes

Finalized multi-service production-ready release.

What's included
- Durable Postgres-backed job queue with Alembic migrations
- Safe multi-worker dequeue: Postgres SKIP LOCKED, SQLite fallback
- Visibility timeout + reclaim stuck jobs
- Sandboxed containerized job runner (Docker-based)
- Migrate one-shot service in docker-compose.prod.yml
- Prometheus metrics: job counters, queued gauge, reclaimed counters
- Worker with periodic reclaim loop and optional sandbox execution
- Frontend + backend integration preserved: submit audit -> queue -> worker -> report

Quick start (local with Docker Compose)
1. Build and start infra:
   docker compose -f docker-compose.prod.yml up -d postgres redis minio

2. Run migrations:
   docker compose -f docker-compose.prod.yml run --rm migrate

3. Build images and start backend + worker:
   docker compose -f docker-compose.prod.yml build
   docker compose -f docker-compose.prod.yml up -d backend worker frontend

4. Enable sandbox execution (optional): set SANDBOX_ENABLED=1 and SANDBOX_IMAGE to the sandbox image tag.

Notes
- Use a real secret manager for DB and S3 credentials in production.
- For high-scale, run workers with Redis-enabled queueing and scale workers horizontally.
- For secure execution, consider Kubernetes Jobs or hardened runtimes (gVisor/Kata).
