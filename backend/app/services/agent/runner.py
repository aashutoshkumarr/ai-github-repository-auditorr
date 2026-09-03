from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.services.repo_fetcher import RepositoryContext
from backend.app.services.agent.context_manager import ContextManager
from backend.app.services.agent.orchestrator import AgentOrchestrator
from backend.app.services.agent.response_engine import ResponseEngine


class AgentRunner:
    """
    Central AI Entrypoint:
    User Input ➔ Context Manager ➔ Central AI Orchestrator ➔ Repository Agent / Direct Answer ➔ Response Engine & Validation ➔ User
    """

    @staticmethod
    async def run(
        ctx: RepositoryContext,
        query: str,
        history: List[Dict[str, str]] = None,
        llm_provider: str = "offline",
        api_key: str = None,
        report: Any = None,
        db: Optional[AsyncSession] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        # Step 1: Build Rich Session & Sliding Window Context
        context = ContextManager.build_context(
            query=query,
            history=history,
            ctx=ctx,
            report=report
        )

        provider = llm_provider
        key = api_key
        if not key or provider == "offline":
            if settings.GEMINI_API_KEY:
                provider = "gemini"
                key = settings.GEMINI_API_KEY
            elif settings.OPENAI_API_KEY:
                provider = "openai"
                key = settings.OPENAI_API_KEY

        # Step 2: Central AI Brain / Orchestrator (Reason, Decide, Route)
        raw_reply, tool_steps, trace = await AgentOrchestrator.process(
            context=context,
            ctx=ctx,
            report=report,
            db=db,
            llm_provider=provider,
            api_key=key
        )

        # Step 3: Response Engine & Validation (AST syntax check, clean formatting)
        final_reply = ResponseEngine.validate_and_format(raw_reply)
        return final_reply, tool_steps
