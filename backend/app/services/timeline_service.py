from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import AsyncSessionLocal
from backend.app.models.database_models import (
    AuditReport,
    Repository,
    Finding,
    RepositoryHealthTimeline,
)
from backend.app.models.schemas import TimelinePoint, TimelineResponse


class TimelineService:
    """
    Manages repository audit score history and health trend analytics.
    Tracks chronological audits: e.g. 96 -> 91 -> 87 -> 94, regression flags, and category score deltas.
    """

    @classmethod
    async def record_snapshot(
        cls,
        report_id: str,
        commit_sha: Optional[str] = None,
        commit_message: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> Optional[RepositoryHealthTimeline]:
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            stmt = select(AuditReport).where(AuditReport.id == report_id)
            res = await db.execute(stmt)
            report = res.scalars().first()
            if not report:
                return None

            # Count findings by severity
            f_stmt = select(Finding).where(Finding.report_id == report_id)
            f_res = await db.execute(f_stmt)
            findings = f_res.scalars().all()

            crit_count = sum(1 for f in findings if f.severity.lower() == "critical")
            high_count = sum(1 for f in findings if f.severity.lower() == "high")
            med_count = sum(1 for f in findings if f.severity.lower() == "medium")
            low_count = sum(1 for f in findings if f.severity.lower() in ("low", "informational"))

            timeline_entry = RepositoryHealthTimeline(
                repo_id=report.repo_id,
                report_id=report.id,
                overall_score=report.overall_score,
                security_score=report.security_score,
                quality_score=report.quality_score,
                testing_score=report.testing_score,
                docs_score=report.docs_score,
                deps_score=report.deps_score,
                arch_score=report.arch_score,
                maintainability_score=report.maintainability_score,
                findings_count=len(findings),
                critical_count=crit_count,
                high_count=high_count,
                medium_count=med_count,
                low_count=low_count,
                commit_sha=commit_sha,
                commit_message=commit_message,
                created_at=report.created_at or datetime.utcnow(),
            )
            db.add(timeline_entry)
            await db.commit()
            return timeline_entry
        finally:
            if should_close:
                await db.close()

    @classmethod
    async def get_timeline(
        cls,
        repo_id_or_report_id: str,
        db: Optional[AsyncSession] = None,
    ) -> TimelineResponse:
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        try:
            # Check if repo_id or report_id was provided
            repo_stmt = select(Repository).where(Repository.id == repo_id_or_report_id)
            repo_res = await db.execute(repo_stmt)
            repo = repo_res.scalars().first()

            if not repo:
                rep_stmt = select(AuditReport).where(AuditReport.id == repo_id_or_report_id)
                rep_res = await db.execute(rep_stmt)
                report = rep_res.scalars().first()
                if report:
                    r_stmt = select(Repository).where(Repository.id == report.repo_id)
                    r_res = await db.execute(r_stmt)
                    repo = r_res.scalars().first()

            if not repo:
                return TimelineResponse(
                    repo_id=repo_id_or_report_id,
                    repo_name="Repository",
                    repo_url="",
                    points=[],
                    trend="Stable",
                    average_score=0.0,
                    latest_score=0.0,
                    score_delta=0.0,
                    has_regression=False,
                )

            # Fetch all timeline points ordered chronologically
            entries_stmt = (
                select(RepositoryHealthTimeline)
                .where(RepositoryHealthTimeline.repo_id == repo.id)
                .order_by(RepositoryHealthTimeline.created_at.asc())
            )
            entries_res = await db.execute(entries_stmt)
            entries = entries_res.scalars().all()

            # If no timeline rows exist yet, populate from existing audit reports
            if not entries:
                rep_list_stmt = (
                    select(AuditReport)
                    .where(AuditReport.repo_id == repo.id)
                    .order_by(AuditReport.created_at.asc())
                )
                rep_list_res = await db.execute(rep_list_stmt)
                reports = rep_list_res.scalars().all()
                for r in reports:
                    await cls.record_snapshot(r.id, db=db)

                entries_res = await db.execute(entries_stmt)
                entries = entries_res.scalars().all()

            points: List[TimelinePoint] = []
            for e in entries:
                points.append(
                    TimelinePoint(
                        audit_id=e.report_id,
                        created_at=e.created_at,
                        overall_score=round(e.overall_score, 1),
                        security_score=round(e.security_score, 1),
                        quality_score=round(e.quality_score, 1),
                        testing_score=round(e.testing_score, 1),
                        docs_score=round(e.docs_score, 1),
                        deps_score=round(e.deps_score, 1),
                        arch_score=round(e.arch_score, 1),
                        maintainability_score=round(e.maintainability_score, 1),
                        findings_count=e.findings_count,
                        critical_count=e.critical_count,
                        high_count=e.high_count,
                        medium_count=e.medium_count,
                        low_count=e.low_count,
                        commit_sha=e.commit_sha,
                        commit_message=e.commit_message,
                    )
                )

            if not points:
                return TimelineResponse(
                    repo_id=repo.id,
                    repo_name=repo.name,
                    repo_url=repo.url,
                    points=[],
                    trend="Stable",
                    average_score=0.0,
                    latest_score=0.0,
                    score_delta=0.0,
                    has_regression=False,
                )

            avg_score = round(sum(p.overall_score for p in points) / len(points), 1)
            latest_score = points[-1].overall_score
            first_score = points[0].overall_score
            score_delta = round(latest_score - first_score, 1)

            trend = "Stable"
            if len(points) >= 2:
                recent_delta = points[-1].overall_score - points[-2].overall_score
                if recent_delta > 1.5:
                    trend = "Improving"
                elif recent_delta < -1.5:
                    trend = "Degrading"

            has_regression = False
            if len(points) >= 2 and (points[-1].overall_score < points[-2].overall_score - 4.0):
                has_regression = True

            return TimelineResponse(
                repo_id=repo.id,
                repo_name=repo.name,
                repo_url=repo.url,
                points=points,
                trend=trend,
                average_score=avg_score,
                latest_score=latest_score,
                score_delta=score_delta,
                has_regression=has_regression,
            )
        finally:
            if should_close:
                await db.close()
