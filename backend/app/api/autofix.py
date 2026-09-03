from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.schemas import (
    AutoFixGenerateRequest,
    AutoFixProposalResponse,
    AutoFixVerifyRequest,
    AutoFixVerifyResponse,
    AutoFixCreatePRRequest,
    AutoFixCreatePRResponse,
)
from backend.app.services.autofix_orchestrator import AutoFixOrchestrator

router = APIRouter(prefix="/audit", tags=["Auto-Fix & Verification"])


@router.post("/{report_id}/autofix/generate", response_model=AutoFixProposalResponse)
async def generate_autofix_proposal(
    report_id: str,
    req: AutoFixGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Diagnoses finding root cause and generates a syntax-validated candidate code patch and unified diff preview.
    """
    try:
        proposal = await AutoFixOrchestrator.generate_proposal(
            report_id=report_id,
            finding_id=req.finding_id,
            llm_provider=req.llm_provider or "offline",
            api_key=req.api_key,
            db=db,
        )
        return proposal
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate fix proposal: {exc}")


@router.post("/{report_id}/autofix/verify", response_model=AutoFixVerifyResponse)
async def verify_autofix_patch(
    report_id: str,
    req: AutoFixVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Applies the candidate patch inside an isolated sandbox, executes tests, runs security re-scan, and computes score delta.
    """
    try:
        verify_res = await AutoFixOrchestrator.apply_and_verify(
            report_id=report_id,
            finding_id=req.finding_id,
            session_id=req.session_id,
            patched_code=req.patched_code,
            run_tests=req.run_tests,
            db=db,
        )
        return verify_res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Verification failed: {exc}")


@router.post("/{report_id}/autofix/create-pr", response_model=AutoFixCreatePRResponse)
async def create_autofix_pull_request(
    report_id: str,
    req: AutoFixCreatePRRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Creates an automated GitHub Pull Request with full test execution logs and verification provenance.
    """
    try:
        pr_res = await AutoFixOrchestrator.create_pull_request(
            report_id=report_id,
            finding_id=req.finding_id,
            session_id=req.session_id,
            github_token=req.github_token,
            branch_name=req.branch_name,
            title=req.title,
            description=req.description,
            db=db,
        )
        return pr_res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PR creation failed: {exc}")
