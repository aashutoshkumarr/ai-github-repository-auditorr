from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.database_models import AuditReport
from backend.app.services.repo_fetcher import RepoFetcher
from backend.app.services.rag.qa_engine import CodebaseQAEngine

router = APIRouter(prefix="/rag", tags=["Codebase RAG"])

class RAGQueryRequest(BaseModel):
    report_id: str
    query: str

class CitationItem(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    snippet: str
    relevance_score: float
    symbol: str

class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[CitationItem]

@router.post("/query", response_model=RAGQueryResponse)
async def query_codebase_rag(request: RAGQueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Executes semantic RAG query over the audited codebase and returns evidence-backed citations.
    """
    stmt = (
        select(AuditReport)
        .where(AuditReport.id == request.report_id)
        .options(selectinload(AuditReport.repository))
    )
    res = await db.execute(stmt)
    report = res.scalars().first()

    if not report or not report.repository:
        raise HTTPException(status_code=404, detail="Audit report or repository not found")

    try:
        ctx = await RepoFetcher.fetch_repository(report.repository.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load repository: {str(e)}")

    qa_result = CodebaseQAEngine.answer_query(ctx, request.query)
    return RAGQueryResponse(**qa_result)
