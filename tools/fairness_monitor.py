"""
Disparate Impact Monitoring Tool
=================================
Standalone compliance utility for NIST AI RMF "Measure" capability.

Queries the `node_audit_logs` table produced by the decisioning agent's
audit decorator and computes approval-rate distributions grouped by risk
tier and triggered reason keys.  Outputs a markdown-formatted compliance
report to stdout.

Usage:
    python tools/fairness_monitor.py                       # uses DATABASE_GENERIC env var
    python tools/fairness_monitor.py --db <connection_url>  # explicit connection
"""

import argparse
import asyncio
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import Column, DateTime, Integer, String, Text, text
from sqlalchemy import Uuid as SAUuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from sqlalchemy import select

Base = declarative_base()


# ---------------------------------------------------------------------------
# Mirror of the NodeAuditLog model (read-only, no migrations)
# ---------------------------------------------------------------------------
class NodeAuditLog(Base):
    __tablename__ = "node_audit_logs"

    id: Mapped[Any] = mapped_column(SAUuid, primary_key=True)
    application_id: Mapped[str] = mapped_column(String(50))
    agent_name: Mapped[str] = mapped_column(String(50))
    node_name: Mapped[str] = mapped_column(String(100))
    input_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True))


# ---------------------------------------------------------------------------
# Data retrieval
# ---------------------------------------------------------------------------
async def fetch_decision_logs(db_url: str) -> List[Dict[str, Any]]:
    """Return all decision_llm_node audit rows as dicts."""
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        stmt = (
            select(NodeAuditLog)
            .where(NodeAuditLog.node_name == "decision_llm_node")
            .where(NodeAuditLog.status == "SUCCESS")
            .order_by(NodeAuditLog.created_at)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()

    await engine.dispose()
    return [
        {
            "application_id": r.application_id,
            "output_summary": r.output_summary or {},
            "output_state": r.output_state or {},
            "created_at": r.created_at,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------
def _extract_decision(row: Dict[str, Any]) -> str:
    return (
        row["output_summary"].get("decision")
        or row["output_state"].get("final_decision", {}).get("decision")
        or "UNKNOWN"
    )


def _extract_risk_tier(row: Dict[str, Any]) -> str:
    return (
        row["output_summary"].get("risk_tier")
        or row["output_state"].get("final_decision", {}).get("risk_tier")
        or "UNKNOWN"
    )


def _extract_reason_keys(row: Dict[str, Any]) -> List[str]:
    keys = row["output_summary"].get("triggered_reason_keys") or []
    if not keys:
        fd = row["output_state"].get("final_decision", {})
        keys = [k for k in [fd.get("primary_reason_key"), fd.get("secondary_reason_key")] if k]
    return keys


def compute_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute approval rates, reason distributions, and flag disparities."""
    total = len(rows)
    if total == 0:
        return {"total": 0, "warning": "No decision logs found."}

    # --- Overall decision distribution ---
    decision_counts: Counter = Counter()
    for r in rows:
        decision_counts[_extract_decision(r)] += 1

    # --- Per risk-tier decision distribution ---
    tier_decisions: Dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        tier = _extract_risk_tier(r)
        decision = _extract_decision(r)
        tier_decisions[tier][decision] += 1

    # --- Reason key frequency ---
    reason_counts: Counter = Counter()
    for r in rows:
        for key in _extract_reason_keys(r):
            reason_counts[key] += 1

    # --- Disparate impact flag ---
    # Check if any risk tier has an approval rate that varies
    # significantly from the overall approval rate.
    overall_approve_rate = decision_counts.get("APPROVE", 0) / total if total else 0
    tier_flags: List[Dict[str, Any]] = []
    for tier, counts in sorted(tier_decisions.items()):
        tier_total = sum(counts.values())
        tier_approve = counts.get("APPROVE", 0) / tier_total if tier_total else 0
        if overall_approve_rate > 0:
            ratio = tier_approve / overall_approve_rate
        else:
            ratio = 0.0
        flag = "⚠️ REVIEW" if ratio < 0.80 and tier_total >= 3 else "✅ OK"
        tier_flags.append({
            "tier": tier,
            "total": tier_total,
            "approve_rate": round(tier_approve * 100, 1),
            "ratio_to_overall": round(ratio, 3),
            "flag": flag,
        })

    return {
        "total": total,
        "overall_decision_distribution": dict(decision_counts.most_common()),
        "overall_approve_rate_pct": round(overall_approve_rate * 100, 1),
        "tier_analysis": tier_flags,
        "top_decline_reasons": dict(reason_counts.most_common(10)),
    }


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------
def render_report(metrics: Dict[str, Any]) -> str:
    lines: List[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"# Disparate Impact Monitoring Report")
    lines.append(f"*Generated: {now}*\n")

    if metrics.get("warning"):
        lines.append(f"> [!WARNING]\n> {metrics['warning']}\n")
        return "\n".join(lines)

    lines.append(f"**Total Applications Evaluated:** {metrics['total']}\n")

    # Overall distribution
    lines.append("## Overall Decision Distribution\n")
    lines.append("| Decision | Count | % |")
    lines.append("| :--- | ---: | ---: |")
    for decision, count in metrics["overall_decision_distribution"].items():
        pct = round(count / metrics["total"] * 100, 1)
        lines.append(f"| {decision} | {count} | {pct}% |")
    lines.append("")

    # Per-tier analysis
    lines.append("## Risk Tier Approval Analysis\n")
    lines.append("> Disparate impact flag triggers when a tier's approval rate is below 80% of the overall rate (4/5ths rule).\n")
    lines.append("| Risk Tier | Applications | Approval Rate | Ratio to Overall | Status |")
    lines.append("| :--- | ---: | ---: | ---: | :--- |")
    for t in metrics["tier_analysis"]:
        lines.append(
            f"| {t['tier']} | {t['total']} | {t['approve_rate']}% | {t['ratio_to_overall']} | {t['flag']} |"
        )
    lines.append("")

    # Top decline reasons
    lines.append("## Top Decline Reason Keys\n")
    lines.append("| Reason Key | Occurrences |")
    lines.append("| :--- | ---: |")
    for key, count in metrics["top_decline_reasons"].items():
        lines.append(f"| `{key}` | {count} |")
    lines.append("")

    # Summary
    flagged = [t for t in metrics["tier_analysis"] if "REVIEW" in t["flag"]]
    if flagged:
        lines.append("> [!CAUTION]")
        lines.append(f"> {len(flagged)} risk tier(s) flagged for potential disparate impact. Manual review recommended.\n")
    else:
        lines.append("> [!NOTE]")
        lines.append("> No disparate impact flags detected. All tiers within acceptable thresholds.\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
async def main(db_url: str) -> None:
    rows = await fetch_decision_logs(db_url)
    metrics = compute_metrics(rows)
    report = render_report(metrics)
    print(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Disparate Impact Monitoring for Underwriting Decisions")
    parser.add_argument(
        "--db",
        default=os.getenv(
            "DATABASE_GENERIC",
            "postgresql+asyncpg://test_user:test_password@localhost:5432/bfsi_db",
        ),
        help="Async SQLAlchemy database URL (default: DATABASE_GENERIC env var)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.db))
