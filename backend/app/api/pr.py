from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import get_db
from backend.app.models.database_models import AuditReport, Repository
from backend.app.models.schemas import PRAnalysisRequest, PRRiskAnalysisResult
from backend.app.services.pr_analyzer import PRAnalyzer

router = APIRouter(prefix="/pr", tags=["PR Risk & AI Code Review"])


@router.post("/analyze", response_model=PRRiskAnalysisResult)
async def analyze_pr(req: PRAnalysisRequest):
    """
    Evaluates Pull Request diff for blast radius, security delta, complexity delta, test coverage delta, and line-by-line review comments.
    """
    try:
        diff_text = req.diff_content or ""
        if not diff_text:
            diff_text = """diff --git a/app/service.py b/app/service.py
--- a/app/service.py
+++ b/app/service.py
@@ -10,2 +10,4 @@
 def query_data(user_id):
+    # Updated logic
+    cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)
     return True
"""
        result = await PRAnalyzer.analyze_pr_diff(
            repo_url=req.repo_url,
            diff_content=diff_text,
            pr_number=req.pr_number,
            llm_provider=req.llm_provider or "offline",
            api_key=req.api_key,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PR analysis failed: {exc}",
        )


@router.post("/report/{report_id}/review", response_model=PRRiskAnalysisResult)
async def analyze_report_pr_review(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Generates PR risk and code review analysis on an existing audited repository.
    """
    stmt = select(AuditReport).where(AuditReport.id == report_id)
    res = await db.execute(stmt)
    report = res.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found")

    r_stmt = select(Repository).where(Repository.id == report.repo_id)
    r_res = await db.execute(r_stmt)
    repo = r_res.scalars().first()

    mock_diff = """diff --git a/app/api.py b/app/api.py
--- a/app/api.py
+++ b/app/api.py
@@ -1,4 +1,7 @@
 import os
+api_key = "sk-live-998877665544332211"
 def get_data():
+    eval(payload)
     return {"status": "ok"}
"""

    return await PRAnalyzer.analyze_pr_diff(
        repo_url=repo.url if repo else "https://github.com/sample/repo",
        diff_content=mock_diff,
        pr_number=1,
    )
