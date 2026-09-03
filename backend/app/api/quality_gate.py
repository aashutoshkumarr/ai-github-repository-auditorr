from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.schemas import (
    QualityGateEvaluateRequest,
    QualityGateResult,
    QualityGatePolicy,
)
from backend.app.services.quality_gate import QualityGateEngine

router = APIRouter(prefix="/audit", tags=["CI/CD Quality Gate"])


@router.post("/{report_id}/quality-gate/evaluate", response_model=QualityGateResult)
async def evaluate_quality_gate(
    report_id: str,
    req: QualityGateEvaluateRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates repository audit report against DevSecOps Quality Gate policies for CI/CD merge decisions.
    """
    try:
        policy = req.policy if req else QualityGatePolicy()
        result = await QualityGateEngine.evaluate(report_id, policy=policy, db=db)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality gate evaluation failed: {exc}",
        )


@router.get("/{report_id}/quality-gate", response_model=QualityGateResult)
async def get_quality_gate(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves default quality gate assessment for an audit report.
    """
    try:
        result = await QualityGateEngine.evaluate(report_id, db=db)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality gate retrieval failed: {exc}",
        )
