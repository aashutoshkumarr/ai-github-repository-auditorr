from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header, Request

from backend.app.core.config import settings
from backend.app.models.schemas import AuditRequest
from backend.app.services.job_queue import job_queue

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/health")
async def jobs_health() -> Dict[str, Any]:
    return await job_queue.health()


@router.get("")
async def list_jobs() -> Dict[str, Any]:
    jobs = await job_queue.list_jobs()
    return {"jobs": [job.to_public_dict() for job in jobs]}


@router.post("/submit")
async def submit_job(request: AuditRequest, x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> Dict[str, Any]:
    # Basic validation
    if not request.github_url or not request.github_url.strip():
        raise HTTPException(status_code=400, detail="GitHub URL is required")

    # Resolve tenant via API key if configured
    tenant = None
    if getattr(settings, 'API_KEYS', None):
        if not x_api_key:
            raise HTTPException(status_code=401, detail="Missing X-API-Key header")
        tenant = settings.API_KEYS.get(x_api_key)
        if not tenant:
            raise HTTPException(status_code=403, detail="Invalid API key")

    # Rate limiting (best-effort via Redis)
    if job_queue._redis and tenant:
        try:
            k = f"ratelimit:{tenant}"
            val = await job_queue._redis.incr(k)
            if val == 1:
                await job_queue._redis.expire(k, 60)
            limit = int(getattr(settings, 'RATE_LIMIT_PER_MIN', 60))
            if val > limit:
                raise HTTPException(status_code=429, detail="Rate limit exceeded for tenant")
        except HTTPException:
            raise
        except Exception:
            # best-effort - do not block on rate-limit backend failures
            pass

    # Inject tenant and webhook into request payload
    payload = request.model_dump(exclude_none=True)
    if tenant:
        payload['tenant_id'] = tenant
    if request.webhook_url:
        payload['webhook_url'] = request.webhook_url

    job = await job_queue.enqueue(payload)
    return {
        "message": "Audit job queued successfully",
        "job": job.to_public_dict(),
    }


@router.get("/{job_id}")
async def get_job(job_id: str) -> Dict[str, Any]:
    job = await job_queue.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job.to_public_dict()}


@router.get("/service")
async def service_status() -> Dict[str, Any]:
    return {
        "service": settings.PROJECT_NAME,
        "queue_backend": "redis" if settings.REDIS_URL else "local-memory",
        "storage_backend": settings.STORAGE_BACKEND,
        "status": "online",
    }
