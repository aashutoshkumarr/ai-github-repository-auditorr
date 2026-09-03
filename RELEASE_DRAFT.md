# Draft Release: v0.1.0 — Production-ready Auditor Platform

This is a draft GitHub Release for the AI GitHub Repository Auditor project. It bundles the production-readiness work: durable Postgres-backed job queue, sandboxed runners, Alembic migrations, Prometheus metrics hooks, Docker Compose production example, and CI workflow.

Highlights

- Production-grade job queue
  - Async SQLAlchemy + Postgres (asyncpg) durable store for audit_jobs and pending_jobs
  - SKIP LOCKED dequeue for safe multi-worker operation and SQLite fallback for local dev
  - Visibility timeouts and automatic reclaim of stuck jobs
- Sandboxed execution
  - Per-job sandbox runner image to analyze untrusted repos in isolated containers
  - Worker integration to spawn sandbox containers with resource/time limits
- Migrations & Schema
  - Alembic scaffolding and initial migrations (0001..0004) to create job tables and indexes
  - run_migrations helper to apply migrations using project DATABASE_URL
- Observability
  - Prometheus metrics for enqueued/completed/failed/reclaimed jobs
  - Example docker-compose.prod.yml including a migrate one-shot service
- Developer & CI
  - GitHub Actions workflow to run backend tests and build frontend and images
  - CHANGELOG.md and RELEASE_NOTES.md included with deploy instructions

Breaking / Important Notes

- SANDBOX_ENABLED defaults to false for local dev. Running the sandbox requires a host/container runtime. Do not enable sandbox on hosts that you cannot fully control.
- For SKIP LOCKED to work correctly, use a Postgres DSN with the asyncpg dialect (e.g. postgresql+asyncpg://...)
- Secrets (DB, S3, Redis, registry) are currently read from env vars; replace with a secret manager in production.

How to publish this draft release

If you have a GitHub token and repo remote configured, create a release using the gh CLI or the GitHub Releases API:

- With gh CLI (recommended):
  gh release create v0.1.0 --title "v0.1.0 — Production-ready Auditor Platform" --notes-file RELEASE_DRAFT.md --draft

- With curl (API):
  curl -X POST -H "Authorization: token $GITHUB_TOKEN" -H "Content-Type: application/json" \
    https://api.github.com/repos/OWNER/REPO/releases \
    -d '{"tag_name":"v0.1.0","name":"v0.1.0 — Production-ready Auditor Platform","body":"<paste notes>","draft":true}'

Local fallback

A RELEASE_DRAFT.md has been committed to the repository so you can review, edit, and publish manually if needed.

Changelog

See CHANGELOG.md for the full list of changes and migration notes.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
