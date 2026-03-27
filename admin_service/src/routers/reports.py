"""
Reporting & Analytics API — Phase 5.
All endpoints are read-only aggregations across admin_db and agent DBs.

GET /reports/dashboard          — OFFICER+
GET /reports/applications       — OFFICER+
GET /reports/risk-distribution  — OFFICER+
GET /reports/disbursements      — OFFICER+
GET /reports/review-performance — MANAGER+
"""
from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["reports"])

# Endpoint implementations are added below by parallel agents.
# Each endpoint is self-contained and imports only what it needs.

from src.routers._reports_dashboard import router as _dashboard_router          # noqa: E402
from src.routers._reports_applications import router as _applications_router    # noqa: E402
from src.routers._reports_risk import router as _risk_router                    # noqa: E402
from src.routers._reports_disbursements import router as _disbursements_router  # noqa: E402
from src.routers._reports_performance import router as _performance_router      # noqa: E402

router.include_router(_dashboard_router)
router.include_router(_applications_router)
router.include_router(_risk_router)
router.include_router(_disbursements_router)
router.include_router(_performance_router)
