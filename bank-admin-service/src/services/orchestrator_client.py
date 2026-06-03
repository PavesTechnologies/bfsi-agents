"""HTTP client for calling the orchestrator from bank-admin-service."""
import asyncio
from typing import Any, Dict, List, Optional

import httpx

from src.core.config import get_settings


class OrchestratorClient:
    def __init__(self) -> None:
        self._base = get_settings().ORCHESTRATOR_URL

    async def trigger_decisioning(
        self, external_application_id: str, active_analyzers: Optional[List[str]]
    ) -> None:
        """Fire-and-forget: ask the orchestrator to run decisioning for one application."""
        payload: Dict[str, Any] = {"active_analyzers": active_analyzers}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self._base}/internal/run-decisioning/{external_application_id}",
                json=payload,
            )
            resp.raise_for_status()

    async def notify_bank_decision(
        self,
        external_application_id: str,
        final_decision: str,
        approved_amount: Optional[float],
        interest_rate: Optional[float],
        tenure_months: Optional[int],
        monthly_emi: Optional[float],
        counter_offer_options: Optional[List[Any]],
    ) -> None:
        """Tell the orchestrator to push the bank's final decision SSE event to the applicant."""
        payload: Dict[str, Any] = {
            "final_decision": final_decision,
            "approved_amount": approved_amount,
            "interest_rate": interest_rate,
            "tenure_months": tenure_months,
            "monthly_emi": monthly_emi,
            "counter_offer_options": counter_offer_options,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self._base}/internal/notify-bank-decision/{external_application_id}",
                json=payload,
            )
            resp.raise_for_status()

    async def notify_manual_counter_offer_init(
        self,
        external_application_id: str,
    ) -> None:
        """Ask the orchestrator to re-open a declined application for a bank-initiated
        manual counter offer (sets the pipeline phase to AWAITING_COUNTER_OFFER_REVIEW)
        so the standard publish → select flow applies."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self._base}/internal/counter-offer-manual-init/{external_application_id}",
            )
            resp.raise_for_status()

    async def notify_counter_offers_published(
        self,
        external_application_id: str,
        current_options: List[Any],
    ) -> None:
        """Push a BANK_COUNTER_OFFERS_PUBLISHED SSE event to the applicant's stream.

        Called after a bank employee publishes counter offers so the applicant
        frontend receives the offer list and can present the selection UI.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self._base}/internal/counter-offers-published/{external_application_id}",
                json={"current_options": current_options},
            )
            resp.raise_for_status()
