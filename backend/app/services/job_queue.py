import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import select, delete, func, text
from sqlalchemy.dialects.postgresql import insert

from backend.app.core.config import settings
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.database_models import AuditJobModel, PendingJobModel

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover - optional dependency for production deployments
    redis = None


class AuditJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: str = "queued"
    stage: str = "queued"
    percent_complete: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    request: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = None
    webhook_url: Optional[str] = None
    report_id: Optional[str] = None
    error: Optional[str] = None

    def to_public_dict(self) -> Dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["created_at"] = self.created_at.isoformat()
        payload["updated_at"] = self.updated_at.isoformat()
        return payload


class JobQueueManager:
    def __init__(self) -> None:
        # Metrics (prometheus counters/gauges)
        try:
            from prometheus_client import Counter, Gauge

            ns = getattr(settings, "PROMETHEUS_NAMESPACE", "auditor")

            self._ctr_enqueued = Counter(
                f"{ns}_jobs_enqueued_total",
                "Total jobs enqueued",
            )
            self._ctr_completed = Counter(
                f"{ns}_jobs_completed_total",
                "Total jobs completed",
            )
            self._ctr_failed = Counter(
                f"{ns}_jobs_failed_total",
                "Total jobs failed",
            )
            self._gauge_queued = Gauge(
                f"{ns}_jobs_queued",
                "Current queued jobs",
            )

            # Reclamation metrics
            self._ctr_reclaimed = Counter(
                f"{ns}_jobs_reclaimed_total",
                "Total jobs reclaimed after visibility timeout",
            )
            self._ctr_reclaim_errors = Counter(
                f"{ns}_jobs_reclaim_errors_total",
                "Total errors encountered while reclaiming stuck jobs",
            )

        except Exception:
            self._ctr_enqueued = None
            self._ctr_completed = None
            self._ctr_failed = None
            self._gauge_queued = None
            self._ctr_reclaimed = None
            self._ctr_reclaim_errors = None

        self._jobs: Dict[str, AuditJob] = {}
        self._lock = asyncio.Lock()
        self._redis = None

        if settings.REDIS_URL and redis:
            self._redis = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )

        # Worker identity for locking
        self._worker_id = str(uuid4())

        # Default visibility timeout in seconds for jobs claimed by a worker
        self._visibility_seconds = int(
            getattr(settings, "JOB_VISIBILITY_SECONDS", 300)
        )

        # Ensure DB tables exist when running with Postgres;
        # best-effort (no-op on many test environments)
        try:
            # Schedule background creation of tables if an event loop is running
            loop = asyncio.get_event_loop()

            if loop.is_running():
                loop.create_task(self._ensure_tables())

        except Exception:
            # If event loop isn't available or tasks cannot be scheduled here,
            # we'll rely on first DB access to create tables
            pass

    async def _ensure_tables(self) -> None:
        # Ensure tables exist using SQLAlchemy metadata create_all via an async session
        async with AsyncSessionLocal() as session:
            async with session.begin():
                await session.run_sync(
                    lambda sync_sess: AuditJobModel.metadata.create_all(
                        bind=sync_sess.get_bind()
                    )
                )

    async def enqueue(self, request: Dict[str, Any]) -> AuditJob:
        # Normalize tenant/webhook into top-level job fields when available
        tenant = (
            request.get("tenant_id")
            or request.get("tenant")
            or request.get("tenant_id")
        )
        webhook = request.get("webhook_url") or request.get("webhook")

        job = AuditJob(
            request=request,
            tenant_id=tenant,
            webhook_url=webhook,
        )

        payload = job.to_public_dict()

        async with AsyncSessionLocal() as session:
            async with session.begin():

                # PostgreSQL-compatible UPSERT
                stmt = insert(AuditJobModel).values(
                    job_id=job.id,
                    payload=json.dumps(payload),
                    created_at=job.created_at,
                    updated_at=job.updated_at,
                )

                stmt = stmt.on_conflict_do_update(
                    index_elements=[AuditJobModel.job_id],
                    set_={
                        "payload": stmt.excluded.payload,
                        "created_at": stmt.excluded.created_at,
                        "updated_at": stmt.excluded.updated_at,
                    },
                )

                await session.execute(stmt)

                # Insert pending job if not exists
                stmt2 = insert(PendingJobModel).values(
                    job_id=job.id
                )

                try:
                    stmt2 = stmt2.on_conflict_do_nothing(
                        index_elements=[PendingJobModel.job_id]
                    )
                    await session.execute(stmt2)

                except Exception:
                    # Unique constraint may fail in other database/test environments
                    pass

        self._jobs[job.id] = job

        # Prometheus metric
        try:
            if self._ctr_enqueued is not None:
                self._ctr_enqueued.inc()

            if self._gauge_queued is not None:
                async with AsyncSessionLocal() as session:
                    res = await session.execute(
                        select(func.count(PendingJobModel.job_id))
                    )
                    q = res.scalar() or 0
                    self._gauge_queued.set(q)

        except Exception:
            pass

        if self._redis:
            await self._redis.lpush(
                settings.JOB_QUEUE_NAME,
                json.dumps(payload),
            )

        return job

    async def get_job(self, job_id: str) -> Optional[AuditJob]:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(AuditJobModel).where(
                    AuditJobModel.job_id == job_id
                )
            )

            row = res.scalar_one_or_none()

            if row is not None:
                job = AuditJob.model_validate(
                    json.loads(row.payload)
                )
                self._jobs[job.id] = job
                return job

        return self._jobs.get(job_id)

    async def list_jobs(self) -> List[AuditJob]:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(AuditJobModel).order_by(
                    AuditJobModel.created_at.desc()
                )
            )

            rows = res.scalars().all()

            jobs = [
                AuditJob.model_validate(json.loads(r.payload))
                for r in rows
            ]

            self._jobs = {
                job.id: job
                for job in jobs
            }

            return jobs

    async def dequeue(self) -> Optional[AuditJob]:
        # Try DB-backed pending_jobs first.
        # Use FOR UPDATE SKIP LOCKED on Postgres for safe multi-worker dequeue.
        now = datetime.utcnow()
        visibility_deadline = now + timedelta(
            seconds=self._visibility_seconds
        )

        async with AsyncSessionLocal() as session:

            # Start a transaction so FOR UPDATE locks are held until delete/update
            async with session.begin():

                try:
                    # Try to use SKIP LOCKED (works on Postgres).
                    pending_stmt = (
                        select(PendingJobModel)
                        .order_by(PendingJobModel.seq.asc())
                        .limit(1)
                        .with_for_update(skip_locked=True)
                    )

                    res = await session.execute(pending_stmt)
                    pending = res.scalar_one_or_none()

                except Exception:
                    # Fallback for SQLite or other dialects
                    res = await session.execute(
                        select(PendingJobModel)
                        .order_by(PendingJobModel.seq.asc())
                        .limit(1)
                    )

                    pending = res.scalar_one_or_none()

                if pending is None:
                    # Fallback to Redis if configured
                    if self._redis:
                        raw = await self._redis.rpop(
                            settings.JOB_QUEUE_NAME
                        )

                        if not raw:
                            return None

                        payload = json.loads(raw)

                        job = AuditJob.model_validate(payload)
                        self._jobs[job.id] = job

                        return job

                    return None

                job_id = pending.job_id

                # Claim the job:
                # delete pending row (this will release the lock when transaction commits)
                await session.execute(
                    delete(PendingJobModel).where(
                        PendingJobModel.job_id == job_id
                    )
                )

                # Ensure audit_jobs row exists without overwriting existing data.
                # This is PostgreSQL-compatible.
                stmt = insert(AuditJobModel).values(
                    job_id=job_id,
                    payload=json.dumps({}),
                    created_at=now,
                    updated_at=now,
                )

                stmt = stmt.on_conflict_do_nothing(
                    index_elements=[AuditJobModel.job_id]
                )

                await session.execute(stmt)

                # Update lock metadata
                await session.execute(
                    text(
                        """
                        UPDATE audit_jobs
                        SET
                            locked_by = :locked_by,
                            locked_at = :locked_at,
                            visibility_deadline = :visibility_deadline,
                            updated_at = :updated_at
                        WHERE job_id = :job_id
                        """
                    ),
                    {
                        "locked_by": self._worker_id,
                        "locked_at": now,
                        "visibility_deadline": visibility_deadline,
                        "updated_at": now,
                        "job_id": job_id,
                    },
                )

                # Fetch payload
                res2 = await session.execute(
                    select(AuditJobModel).where(
                        AuditJobModel.job_id == job_id
                    )
                )

                job_row = res2.scalar_one_or_none()

                if job_row is None:
                    return None

                job = AuditJob.model_validate(
                    json.loads(job_row.payload)
                )

                self._jobs[job.id] = job

                return job

    async def update_status(
        self,
        job_id: str,
        *,
        status: str,
        stage: str,
        percent_complete: int,
        report_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[AuditJob]:

        job = await self.get_job(job_id)

        if job is None:
            return None

        job.status = status
        job.stage = stage
        job.percent_complete = percent_complete
        job.report_id = report_id or job.report_id
        job.error = error or job.error
        job.updated_at = datetime.utcnow()

        payload = job.to_public_dict()

        async with AsyncSessionLocal() as session:
            async with session.begin():

                # PostgreSQL-compatible UPSERT
                stmt = insert(AuditJobModel).values(
                    job_id=job.id,
                    payload=json.dumps(payload),
                    created_at=job.created_at,
                    updated_at=job.updated_at,
                )

                stmt = stmt.on_conflict_do_update(
                    index_elements=[AuditJobModel.job_id],
                    set_={
                        "payload": stmt.excluded.payload,
                        "created_at": stmt.excluded.created_at,
                        "updated_at": stmt.excluded.updated_at,
                    },
                )

                await session.execute(stmt)

        # Metrics update
        try:
            if (
                status == "completed"
                and self._ctr_completed is not None
            ):
                self._ctr_completed.inc()

            if (
                status == "failed"
                and self._ctr_failed is not None
            ):
                self._ctr_failed.inc()

            if self._gauge_queued is not None:
                async with AsyncSessionLocal() as s2:
                    res = await s2.execute(
                        select(func.count(PendingJobModel.job_id))
                    )

                    q = res.scalar() or 0
                    self._gauge_queued.set(q)

        except Exception:
            pass

        self._jobs[job.id] = job

        return job

    async def health(self) -> Dict[str, Any]:
        backend = "redis" if self._redis else "postgres/sqlite"

        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(func.count(PendingJobModel.job_id))
            )

            queued = res.scalar() or 0

            res2 = await session.execute(
                select(func.count(AuditJobModel.job_id))
            )

            total = res2.scalar() or 0

        return {
            "status": "ok",
            "backend": backend,
            "queued_jobs": queued,
            "total_jobs": total,
        }

    async def reclaim_stuck_jobs(self) -> int:
        """Find jobs whose visibility_deadline has passed and requeue them.

        Returns the number of jobs reclaimed.
        """

        now = datetime.utcnow()
        reclaimed = 0

        async with AsyncSessionLocal() as session:
            async with session.begin():

                res = await session.execute(
                    select(AuditJobModel)
                    .where(
                        AuditJobModel.visibility_deadline != None
                    )
                    .where(
                        AuditJobModel.visibility_deadline < now
                    )
                )

                rows = res.scalars().all()

                for row in rows:
                    job_id = row.job_id

                    # Clear lock fields
                    await session.execute(
                        text(
                            """
                            UPDATE audit_jobs
                            SET
                                locked_by = NULL,
                                locked_at = NULL,
                                visibility_deadline = NULL,
                                updated_at = :updated_at
                            WHERE job_id = :job_id
                            """
                        ),
                        {
                            "updated_at": now,
                            "job_id": job_id,
                        },
                    )

                    # Re-insert into pending_jobs if not present
                    try:
                        stmt = insert(PendingJobModel).values(
                            job_id=job_id
                        )

                        stmt = stmt.on_conflict_do_nothing(
                            index_elements=[PendingJobModel.job_id]
                        )

                        result = await session.execute(stmt)

                        if result.rowcount:
                            reclaimed += 1

                            try:
                                if self._ctr_reclaimed is not None:
                                    self._ctr_reclaimed.inc()
                            except Exception:
                                pass

                    except Exception:
                        # Ignore unique constraint / unsupported dialect errors
                        pass

        try:
            if reclaimed and self._ctr_reclaimed is not None:
                # Best-effort metric already incremented per reclaimed job
                pass

        except Exception:
            if self._ctr_reclaim_errors is not None:
                try:
                    self._ctr_reclaim_errors.inc()
                except Exception:
                    pass

        return reclaimed


job_queue = JobQueueManager()