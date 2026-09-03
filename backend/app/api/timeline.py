from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.schemas import TimelineResponse
from backend.app.services.timeline_service import TimelineService

router = APIRouter(prefix="/audit", tags=["Repository Health Timeline"])


@router.get("/{report_id_or_repo_id}/timeline", response_model=TimelineResponse)
async def get_repository_timeline(
    report_id_or_repo_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves chronological repository audit history and health progression trend (e.g. 96 -> 91 -> 87 -> 94).
    """
    try:
        timeline = await TimelineService.get_timeline(report_id_or_repo_id, db=db)
        return timeline
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve timeline: {exc}",
        )
