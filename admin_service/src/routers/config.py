"""
Configuration & Policy Management API.
- GET/PUT /config/risk-tiers   — interest rate bounds per risk tier (A/B/C/F)
- GET/PUT /config/policies     — loan policy key-value store
All mutations require ADMIN role. History endpoints require MANAGER+.
Mutations are append-only: old row deactivated, new row inserted.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ForbiddenException, NotFoundException
from src.db.session import get_admin_db
from src.dependencies import require_admin, require_manager, require_officer
from src.models.admin_models import LenderUser, LoanPolicy, RiskTierConfig
from src.schemas.config import (
    LoanPolicySchema,
    PaginatedPolicyHistory,
    PaginatedRiskTierHistory,
    RiskTierConfigSchema,
    UpdatePolicyRequest,
    UpdateRiskTierRequest,
)

router = APIRouter(prefix="/config", tags=["config"])

VALID_TIERS = {"A", "B", "C", "F"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tier_to_schema(row: RiskTierConfig, creator_name: Optional[str] = None) -> RiskTierConfigSchema:
    return RiskTierConfigSchema(
        id=str(row.id),
        tier=row.tier,
        min_interest_rate=row.min_interest_rate,
        max_interest_rate=row.max_interest_rate,
        default_interest_rate=row.default_interest_rate,
        max_loan_amount=row.max_loan_amount,
        min_loan_amount=row.min_loan_amount,
        min_credit_score=row.min_credit_score,
        max_dti_ratio=row.max_dti_ratio,
        is_active=row.is_active,
        effective_from=row.effective_from,
        created_by=str(row.created_by) if row.created_by else None,
        created_by_name=creator_name,
        created_at=row.created_at,
        notes=row.notes,
    )


def _policy_to_schema(row: LoanPolicy, creator_name: Optional[str] = None) -> LoanPolicySchema:
    return LoanPolicySchema(
        id=str(row.id),
        policy_key=row.policy_key,
        policy_value=row.policy_value,
        description=row.description,
        category=row.category,
        is_active=row.is_active,
        effective_from=row.effective_from,
        created_by=str(row.created_by) if row.created_by else None,
        created_by_name=creator_name,
        created_at=row.created_at,
        notes=row.notes,
    )


async def _load_creator_names(db: AsyncSession, user_ids: list) -> dict:
    """Batch-load full_name for a list of user UUIDs."""
    if not user_ids:
        return {}
    result = await db.execute(
        select(LenderUser.id, LenderUser.full_name).where(LenderUser.id.in_(user_ids))
    )
    return {str(row.id): row.full_name for row in result}


# ---------------------------------------------------------------------------
# Risk Tier — GET active configs
# ---------------------------------------------------------------------------

@router.get("/risk-tiers", response_model=list[RiskTierConfigSchema])
async def get_risk_tiers(
    current_user: LenderUser = Depends(require_officer),
    db: AsyncSession = Depends(get_admin_db),
):
    """Return the current active config for each tier (A, B, C, F)."""
    result = await db.execute(
        select(RiskTierConfig)
        .where(RiskTierConfig.is_active == True)
        .order_by(RiskTierConfig.tier)
    )
    rows = result.scalars().all()

    user_ids = [r.created_by for r in rows if r.created_by]
    names = await _load_creator_names(db, user_ids)

    return [_tier_to_schema(r, names.get(str(r.created_by))) for r in rows]


# ---------------------------------------------------------------------------
# Risk Tier — GET history (paginated)
# ---------------------------------------------------------------------------

@router.get("/risk-tiers/history", response_model=PaginatedRiskTierHistory)
async def get_risk_tier_history(
    tier: Optional[str] = Query(None, description="Filter by tier: A, B, C, or F"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: LenderUser = Depends(require_manager),
    db: AsyncSession = Depends(get_admin_db),
):
    """Full audit history of all risk tier config changes."""
    q = select(RiskTierConfig)
    if tier:
        if tier not in VALID_TIERS:
            raise ForbiddenException(f"Invalid tier '{tier}'. Must be one of A, B, C, F")
        q = q.where(RiskTierConfig.tier == tier)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    rows_result = await db.execute(
        q.order_by(RiskTierConfig.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = rows_result.scalars().all()

    user_ids = [r.created_by for r in rows if r.created_by]
    names = await _load_creator_names(db, user_ids)

    return PaginatedRiskTierHistory(
        total=total,
        page=page,
        page_size=page_size,
        items=[_tier_to_schema(r, names.get(str(r.created_by))) for r in rows],
    )


# ---------------------------------------------------------------------------
# Risk Tier — PUT (deactivate + insert new)
# ---------------------------------------------------------------------------

@router.put("/risk-tiers/{tier}", response_model=RiskTierConfigSchema)
async def update_risk_tier(
    tier: str,
    body: UpdateRiskTierRequest,
    current_user: LenderUser = Depends(require_admin),
    db: AsyncSession = Depends(get_admin_db),
):
    """Versioned update: deactivates current active config, inserts new row. ADMIN only."""
    if tier not in VALID_TIERS:
        raise NotFoundException(f"Unknown tier '{tier}'. Must be one of A, B, C, F")

    # Validate rate ordering
    if not (body.min_interest_rate <= body.default_interest_rate <= body.max_interest_rate):
        raise ForbiddenException(
            "Rate ordering violated: min_interest_rate <= default_interest_rate <= max_interest_rate required"
        )

    # Deactivate current active row(s) for this tier
    await db.execute(
        update(RiskTierConfig)
        .where(RiskTierConfig.tier == tier, RiskTierConfig.is_active == True)
        .values(is_active=False)
    )

    new_row = RiskTierConfig(
        tier=tier,
        min_interest_rate=body.min_interest_rate,
        max_interest_rate=body.max_interest_rate,
        default_interest_rate=body.default_interest_rate,
        max_loan_amount=body.max_loan_amount,
        min_loan_amount=body.min_loan_amount,
        min_credit_score=body.min_credit_score,
        max_dti_ratio=body.max_dti_ratio,
        is_active=True,
        effective_from=body.effective_from,
        created_by=current_user.id,
        notes=body.notes,
    )
    db.add(new_row)
    await db.commit()
    await db.refresh(new_row)

    return _tier_to_schema(new_row, current_user.full_name)


# ---------------------------------------------------------------------------
# Loan Policies — GET active policies
# ---------------------------------------------------------------------------

@router.get("/policies", response_model=list[LoanPolicySchema])
async def get_policies(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: LenderUser = Depends(require_officer),
    db: AsyncSession = Depends(get_admin_db),
):
    """Return all active loan policies, optionally filtered by category."""
    q = select(LoanPolicy).where(LoanPolicy.is_active == True)
    if category:
        q = q.where(LoanPolicy.category == category)
    q = q.order_by(LoanPolicy.category, LoanPolicy.policy_key)

    result = await db.execute(q)
    rows = result.scalars().all()

    user_ids = [r.created_by for r in rows if r.created_by]
    names = await _load_creator_names(db, user_ids)

    return [_policy_to_schema(r, names.get(str(r.created_by))) for r in rows]


# ---------------------------------------------------------------------------
# Loan Policies — GET history (paginated)
# ---------------------------------------------------------------------------

@router.get("/policies/history", response_model=PaginatedPolicyHistory)
async def get_policy_history(
    policy_key: Optional[str] = Query(None, description="Filter by policy_key"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: LenderUser = Depends(require_manager),
    db: AsyncSession = Depends(get_admin_db),
):
    """Full audit history of all loan policy changes."""
    q = select(LoanPolicy)
    if policy_key:
        q = q.where(LoanPolicy.policy_key == policy_key)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    rows_result = await db.execute(
        q.order_by(LoanPolicy.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = rows_result.scalars().all()

    user_ids = [r.created_by for r in rows if r.created_by]
    names = await _load_creator_names(db, user_ids)

    return PaginatedPolicyHistory(
        total=total,
        page=page,
        page_size=page_size,
        items=[_policy_to_schema(r, names.get(str(r.created_by))) for r in rows],
    )


# ---------------------------------------------------------------------------
# Loan Policies — PUT (deactivate + insert new)
# ---------------------------------------------------------------------------

@router.put("/policies/{policy_key}", response_model=LoanPolicySchema)
async def update_policy(
    policy_key: str,
    body: UpdatePolicyRequest,
    current_user: LenderUser = Depends(require_admin),
    db: AsyncSession = Depends(get_admin_db),
):
    """Versioned update: deactivates current active policy, inserts new row. ADMIN only."""
    # Fetch the current active policy to get description + category
    result = await db.execute(
        select(LoanPolicy)
        .where(LoanPolicy.policy_key == policy_key, LoanPolicy.is_active == True)
    )
    current = result.scalar_one_or_none()
    if current is None:
        raise NotFoundException(f"No active policy found for key '{policy_key}'")

    # Deactivate current row
    await db.execute(
        update(LoanPolicy)
        .where(LoanPolicy.policy_key == policy_key, LoanPolicy.is_active == True)
        .values(is_active=False)
    )

    new_row = LoanPolicy(
        policy_key=policy_key,
        policy_value=body.policy_value,
        description=current.description,
        category=current.category,
        is_active=True,
        effective_from=body.effective_from,
        created_by=current_user.id,
        notes=body.notes,
    )
    db.add(new_row)
    await db.commit()
    await db.refresh(new_row)

    return _policy_to_schema(new_row, current_user.full_name)
