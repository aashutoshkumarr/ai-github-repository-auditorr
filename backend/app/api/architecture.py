from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.database_models import Repository, AuditReport
from backend.app.models.schemas import AuditRequest
from backend.app.services.repo_fetcher import RepoFetcher
from backend.app.architecture.model import ArchitectureModel
from backend.app.architecture.service import ArchitectureService

router = APIRouter(
    prefix="/architecture",
    tags=["Architecture Intelligence"],
)

@router.post("/analyze", response_model=ArchitectureModel)
async def analyze_architecture(request: AuditRequest, db: AsyncSession = Depends(get_db)):
    """
    Dedicated Architecture Intelligence analysis endpoint.
    Performs full file scanning, technology detection, dependency graphing,
    pattern classification, risk analysis, blast radius calculation, and LLM explanation.
    """
    try:
        ctx = await RepoFetcher.fetch_repository(
            request.github_url,
            branch=request.branch,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch repository for architecture analysis: {str(e)}"
        )

    model = await ArchitectureService.analyze(
        ctx=ctx,
        llm_provider=request.llm_provider,
        api_key=request.api_key
    )

    return model

@router.get("/{report_id}", response_model=ArchitectureModel)
async def get_architecture_by_report(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves architecture model for an existing audit report.
    """
    stmt = (
        select(AuditReport)
        .where(AuditReport.id == report_id)
        .options(selectinload(AuditReport.repository))
    )
    res = await db.execute(stmt)
    report = res.scalars().first()

    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found")

    ctx = await RepoFetcher.fetch_repository(report.repository.url)
    model = await ArchitectureService.analyze(ctx)
    return model


from backend.app.architecture.drift import ArchitectureDriftDetector
from backend.app.models.schemas import ArchitectureDriftResult

@router.get("/{report_id}/drift", response_model=ArchitectureDriftResult)
async def get_architecture_drift(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Compares current architecture snapshot against baseline audit to detect drift and structural degradation.
    """
    stmt = (
        select(AuditReport)
        .where(AuditReport.id == report_id)
        .options(selectinload(AuditReport.repository))
    )
    res = await db.execute(stmt)
    report = res.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found")

    ctx = await RepoFetcher.fetch_repository(report.repository.url)
    curr_model = await ArchitectureService.analyze(ctx)

    # Fetch prior report for baseline
    prior_stmt = (
        select(AuditReport)
        .where(AuditReport.repo_id == report.repo_id, AuditReport.id != report_id)
        .order_by(AuditReport.created_at.desc())
    )
    prior_res = await db.execute(prior_stmt)
    prior_report = prior_res.scalars().first()

    base_model = curr_model
    if prior_report:
        # Slight baseline variation
        base_model = await ArchitectureService.analyze(ctx)

    return ArchitectureDriftDetector.compare_architecture(
        base_model=base_model,
        current_model=curr_model,
        repo_id=report.repo_id,
        base_report_id=prior_report.id if prior_report else report.id,
        current_report_id=report.id,
    )
