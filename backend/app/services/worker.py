import asyncio
import logging
import traceback
from typing import Optional

import httpx

from backend.app.api.audit import analyze_repository
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.schemas import AuditRequest
from backend.app.services.job_queue import job_queue
from backend.app.core.config import settings

logger = logging.getLogger("auditor.worker")


async def _send_webhook(url: str, payload: dict):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json=payload)
    except Exception:
        # best-effort: do not crash worker on webhook failure
        logger.exception("Failed to send webhook to %s", url)


async def process_job(job_id: str) -> None:
    job = await job_queue.get_job(job_id)
    if job is None:
        return

    await job_queue.update_status(job.id, status="processing", stage="fetching-repository", percent_complete=10)

    request = AuditRequest(**job.request)
    try:
        async with AsyncSessionLocal() as session:
            result = await analyze_repository(request, db=session)

        await job_queue.update_status(
            job.id,
            status="completed",
            stage="verified",
            percent_complete=100,
            report_id=result.id,
        )

        # Notify webhook if requested
        webhook = getattr(job, 'webhook_url', None) or job.request.get('webhook_url')
        if webhook:
            await _send_webhook(webhook, {
                'job_id': job.id,
                'status': 'completed',
                'report_id': result.id,
            })

    except Exception as exc:  # pragma: no cover - worker-level error handling
        tb = traceback.format_exc()
        logger.exception("Error processing job %s: %s", job_id, exc)
        await job_queue.update_status(
            job.id,
            status="failed",
            stage="error",
            percent_complete=100,
            error=str(exc),
        )
        webhook = getattr(job, 'webhook_url', None) or job.request.get('webhook_url')
        if webhook:
            await _send_webhook(webhook, {
                'job_id': job.id,
                'status': 'failed',
                'error': str(exc),
                'traceback': tb,
            })


async def _reclaimer_loop(shutdown_event: asyncio.Event) -> None:
    """Periodically reclaim jobs whose visibility_deadline has passed."""
    interval = int(getattr(settings, 'JOB_RECLAIM_INTERVAL_SECONDS', 60))
    backoff = 1
    max_backoff = 300
    while not shutdown_event.is_set():
        try:
            reclaimed = await job_queue.reclaim_stuck_jobs()
            if reclaimed:
                logger.info("Reclaimed %d stuck jobs", reclaimed)
            # reset backoff on success
            backoff = 1
        except Exception as exc:
            logger.exception("Error reclaiming stuck jobs: %s", exc)
            # exponential backoff on repeated failures
            await asyncio.sleep(backoff)
            backoff = min(max_backoff, backoff * 2)
        # normal interval wait
        await asyncio.wait([shutdown_event.wait()], timeout=interval)


async def worker_loop() -> None:
    shutdown_event = asyncio.Event()

    async def _handle_shutdown():
        logger.info("Worker shutdown requested")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (asyncio.CancelledError,):
        pass

    reclaimer_task = asyncio.create_task(_reclaimer_loop(shutdown_event))

    try:
        while not shutdown_event.is_set():
            job = await job_queue.dequeue()
            if job is None:
                await asyncio.sleep(2)
                continue

            # If sandboxed execution is enabled, run the job inside a short-lived container
            sandbox_enabled = getattr(settings, 'SANDBOX_ENABLED', False)
            if sandbox_enabled:
                # best-effort: run docker container with limited resources
                import shlex
                import subprocess
                image = getattr(settings, 'SANDBOX_IMAGE', 'auditor-sandbox:latest')
                cmd = (
                    f"docker run --rm --network host --memory=512m --cpus=0.5 "
                    f"-e JOB_ID={shlex.quote(job.id)} -e WORKER_ID={shlex.quote(str(job_queue._worker_id))} "
                    f"-e DATABASE_URL={shlex.quote(getattr(settings, 'POSTGRES_URL', getattr(settings, 'DATABASE_URL', ''))) } "
                    f"{image}"
                )
                logger.info("Starting sandbox for job %s: %s", job.id, image)
                try:
                    # Run with timeout equal to visibility window to ensure hung containers are killed by caller
                    timeout = int(getattr(settings, 'JOB_VISIBILITY_SECONDS', 300))
                    proc = await asyncio.create_subprocess_shell(cmd)
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=timeout)
                    except asyncio.TimeoutError:
                        logger.error("Sandbox container timed out for job %s", job.id)
                        proc.kill()
                        await job_queue.update_status(job.id, status='failed', stage='sandbox-timeout', percent_complete=100, error='sandbox timeout')
                        continue
                except Exception as exc:
                    logger.exception("Failed to run sandbox for job %s: %s", job.id, exc)
                    await job_queue.update_status(job.id, status='failed', stage='sandbox-error', percent_complete=100, error=str(exc))
                    continue

                # If the container ran successfully, process_job will have been performed inside the container
                continue

            # Fallback: process in-process
            await process_job(job.id)
    finally:
        logger.info("Worker stopping, cancelling reclaimer")
        reclaimer_task.cancel()
        try:
            await reclaimer_task
        except asyncio.CancelledError:
            logger.info("Reclaimer task cancelled")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(worker_loop())
