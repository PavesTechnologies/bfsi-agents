"""
Reads from the decisioning_agent's underwriting_decisions table.
The bank-admin-service shares the same PostgreSQL instance but uses a different schema.
We query the public schema tables directly.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from src.schemas.application import ApplicationSummary, ApplicationDetail, ApplicationListResponse, DashboardStats, DailyVolume


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_applications(
        self,
        page: int = 1,
        page_size: int = 20,
        decision: Optional[str] = None,
        risk_tier: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> ApplicationListResponse:
        filters = []
        params: dict = {"limit": page_size, "offset": (page - 1) * page_size}

        if decision:
            filters.append("decision = :decision")
            params["decision"] = decision.upper()
        if risk_tier:
            filters.append("risk_tier = :risk_tier")
            params["risk_tier"] = risk_tier.upper()
        if date_from:
            filters.append("created_at >= :date_from")
            params["date_from"] = date_from
        if date_to:
            filters.append("created_at <= :date_to")
            params["date_to"] = date_to

        where_clause = ("WHERE " + " AND ".join(filters)) if filters else ""

        count_query = text(f"SELECT COUNT(*) FROM underwriting_decisions {where_clause}")
        count_result = await self.db.execute(count_query, params)
        total = count_result.scalar_one()

        query = text(f"""
            SELECT application_id, decision, risk_tier, risk_score,
                   approved_amount, interest_rate, tenure_months, created_at
            FROM underwriting_decisions
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        result = await self.db.execute(query, params)
        rows = result.mappings().all()

        items = [ApplicationSummary(**dict(r)) for r in rows]
        return ApplicationListResponse(items=items, total=total, page=page, page_size=page_size)

    async def get_application(self, application_id: str) -> ApplicationDetail:
        result = await self.db.execute(
            text("""
                SELECT application_id, decision, risk_tier, risk_score,
                       approved_amount, disbursement_amount, interest_rate, tenure_months,
                       explanation, decline_reason, reasoning_steps, counter_offer_data,
                       parallel_tasks_executed, node_execution_times, execution_time_ms, created_at
                FROM underwriting_decisions
                WHERE application_id = :app_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"app_id": application_id},
        )
        row = result.mappings().first()
        if not row:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Application not found")
        return ApplicationDetail(**dict(row))

    async def get_dashboard_stats(self, pending_rule_approvals: int = 0) -> DashboardStats:
        result = await self.db.execute(text("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision = 'APPROVE') AS approved,
                COUNT(*) FILTER (WHERE decision = 'DECLINE') AS declined,
                COUNT(*) FILTER (WHERE decision = 'COUNTER_OFFER') AS counter_offer,
                ROUND(AVG(risk_score)::numeric, 2) AS avg_risk_score
            FROM underwriting_decisions
        """))
        row = result.mappings().first()
        total = row["total"] or 0
        approved = row["approved"] or 0

        return DashboardStats(
            total_applications=total,
            total_approved=approved,
            total_declined=row["declined"] or 0,
            total_counter_offer=row["counter_offer"] or 0,
            approval_rate=round(approved / total * 100, 1) if total > 0 else 0.0,
            avg_risk_score=float(row["avg_risk_score"]) if row["avg_risk_score"] else None,
            pending_rule_approvals=pending_rule_approvals,
        )

    async def get_daily_volume(self, days: int = 14) -> list[DailyVolume]:
        result = await self.db.execute(
            text("""
                SELECT
                    DATE(created_at AT TIME ZONE 'UTC') AS date,
                    COUNT(*) FILTER (WHERE decision = 'APPROVE') AS approved,
                    COUNT(*) FILTER (WHERE decision = 'DECLINE') AS declined,
                    COUNT(*) FILTER (WHERE decision = 'COUNTER_OFFER') AS counter_offer,
                    COUNT(*) AS total
                FROM underwriting_decisions
                WHERE created_at >= NOW() - (:days * INTERVAL '1 day')
                GROUP BY DATE(created_at AT TIME ZONE 'UTC')
                ORDER BY date ASC
            """),
            {"days": days},
        )
        rows = result.mappings().all()
        return [DailyVolume(
            date=str(r["date"]),
            approved=r["approved"] or 0,
            declined=r["declined"] or 0,
            counter_offer=r["counter_offer"] or 0,
            total=r["total"] or 0,
        ) for r in rows]
