"""Sandbox runner entrypoint.

This module runs a single job inside the container and exits. It is intended to be
launched by the worker using Docker with restricted resources.

Usage (docker):
  docker run --rm \
    -e DATABASE_URL='postgresql+asyncpg://user:pass@postgres:5432/auditor' \
    -e JOB_ID=<job-id> \
    -e WORKER_ID=<worker-id> \
    my-auditor-sandbox-image

The runner will import the application code and call analyze_repository with a DB session
so reports and job state are persisted directly to the configured DATABASE_URL.
"""
import asyncio
import logging
import os
import traceback
from datetime import datetime, timezone

from backend.app.core.database import AsyncSessionLocal
from backend.app.services.job_queue import job_queue
from backend.app.api.audit import analyze_repository
from backend.app.models.schemas import AuditRequest

logger = logging.getLogger("auditor.sandbox")


async def run_job(job_id: str, worker_id: str) -> None:
    try:
        job = await job_queue.get_job(job_id)
        if job is None:
            logger.error("Job %s not found in job queue", job_id)
            return

        # Claim job in DB (set locked metadata)
        await job_queue.update_status(job_id, status="processing", stage="sandbox", percent_complete=5)

        request = AuditRequest(**job.request)
        async with AsyncSessionLocal() as session:
            result = await analyze_repository(request, db=session)

        await job_queue.update_status(job_id, status="completed", stage="verified", percent_complete=100, report_id=result.id)
        logger.info("Job %s completed inside sandbox, report_id=%s", job_id, result.id)
    except Exception as exc:
        tb = traceback.format_exc()
        logger.exception("Sandbox job %s failed: %s", job_id, exc)
        await job_queue.update_status(job_id, status="failed", stage="sandbox-error", percent_complete=100, error=str(exc))


def main():
    logging.basicConfig(level=logging.INFO)
    job_id = os.getenv('JOB_ID') or None
    worker_id = os.getenv('WORKER_ID') or os.getenv('HOSTNAME')
    if not job_id:
        logger.error('JOB_ID environment variable is required')
        return

    asyncio.run(run_job(job_id, worker_id))


if __name__ == '__main__':
    main()
