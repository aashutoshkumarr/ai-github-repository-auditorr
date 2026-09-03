from fastapi import APIRouter
from backend.app.api.audit import router as audit_router
from backend.app.api.agent import router as agent_router
from backend.app.api.github import router as github_router
from backend.app.api.benchmark import router as benchmark_router
from backend.app.api.samples import router as samples_router
from backend.app.api.rag import router as rag_router
from backend.app.api.repo import router as repo_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.architecture import router as architecture_router
from backend.app.api.autofix import router as autofix_router
from backend.app.api.timeline import router as timeline_router
from backend.app.api.quality_gate import router as quality_gate_router
from backend.app.api.pr import router as pr_router

api_router = APIRouter(prefix="/api")
api_router.include_router(audit_router)
api_router.include_router(agent_router)
api_router.include_router(github_router)
api_router.include_router(benchmark_router)
api_router.include_router(samples_router)
api_router.include_router(rag_router)
api_router.include_router(repo_router)
api_router.include_router(jobs_router)
api_router.include_router(architecture_router)
api_router.include_router(autofix_router)
api_router.include_router(timeline_router)
api_router.include_router(quality_gate_router)
api_router.include_router(pr_router)
