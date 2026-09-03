import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.database_models import AuditReport, Repository
from backend.app.models.schemas import AgentChatRequest, AgentChatResponse
from backend.app.services.repo_fetcher import RepoFetcher
from backend.app.services.agent.runner import AgentRunner

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_repo_agent(request: AgentChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Executes synchronous deep-dive investigation with the AI Repository Copilot Agent.
    """
    stmt = (
        select(AuditReport)
        .where(AuditReport.id == request.report_id)
        .options(
            selectinload(AuditReport.repository),
            selectinload(AuditReport.findings),
            selectinload(AuditReport.dependencies),
            selectinload(AuditReport.hotspots)
        )
    )
    res = await db.execute(stmt)
    report = res.scalars().first()

    if not report or not report.repository:
        raise HTTPException(status_code=404, detail="Repository or audit report not found")

    try:
        ctx = await RepoFetcher.fetch_repository(report.repository.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load repository context: {str(e)}")

    reply, tool_steps = await AgentRunner.run(
        ctx=ctx,
        query=request.message,
        history=request.history,
        llm_provider=request.llm_provider or "offline",
        api_key=request.api_key,
        report=report,
        db=db
    )

    return AgentChatResponse(
        reply=reply,
        tool_steps=[
            {
                "tool_name": ts["tool_name"],
                "tool_input": ts["tool_input"],
                "tool_output": str(ts["tool_output"])[:500]
            }
            for ts in tool_steps
        ]
    )


@router.post("/stream")
async def stream_chat_with_repo_agent(request: AgentChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Server-Sent Events (SSE) streaming endpoint matching OpenAI/ChatGPT/Gemini real-time token streaming.
    Streams autonomous tool pipeline events followed by word-by-word text tokens.
    """
    stmt = (
        select(AuditReport)
        .where(AuditReport.id == request.report_id)
        .options(
            selectinload(AuditReport.repository),
            selectinload(AuditReport.findings),
            selectinload(AuditReport.dependencies),
            selectinload(AuditReport.hotspots)
        )
    )
    res = await db.execute(stmt)
    report = res.scalars().first()

    if not report or not report.repository:
        raise HTTPException(status_code=404, detail="Repository or audit report not found")

    try:
        ctx = await RepoFetcher.fetch_repository(report.repository.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load repository context: {str(e)}")

    reply, tool_steps = await AgentRunner.run(
        ctx=ctx,
        query=request.message,
        history=request.history,
        llm_provider=request.llm_provider or "offline",
        api_key=request.api_key,
        report=report,
        db=db
    )

    async def sse_event_stream():
        # 1. Stream tool pipeline execution events
        for ts in tool_steps:
            event_payload = {
                "type": "tool",
                "data": {
                    "tool_name": ts["tool_name"],
                    "tool_input": ts["tool_input"],
                    "tool_output": str(ts["tool_output"])[:500]
                }
            }
            yield f"data: {json.dumps(event_payload)}\n\n"
            await asyncio.sleep(0.04)

        # 2. Stream tokens with natural typing cadence
        chunks = reply.split(" ")
        for i, word in enumerate(chunks):
            token = word + (" " if i < len(chunks) - 1 else "")
            event_payload = {
                "type": "token",
                "content": token
            }
            yield f"data: {json.dumps(event_payload)}\n\n"
            await asyncio.sleep(0.012)

        # 3. Done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")
