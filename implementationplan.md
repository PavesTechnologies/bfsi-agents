Specification: Counter Offer Selection & Loan Acceptance Confirmation Flow
Overview
Extend the orchestrator pipeline to support two new user-interaction checkpoints:

Counter Offer Selection — When underwriting returns COUNTER_OFFER, pause the pipeline, present 2–3 offer options to the frontend, and resume disbursement only after the user selects one.
Approval Confirmation — When underwriting returns APPROVE, pause the pipeline, present loan terms to the frontend for user acceptance, and resume disbursement only after explicit confirmation.


Current State
The pipeline in execute_full_pipeline is a single-pass synchronous chain:
Intake → KYC → Underwriting → Disbursement
When decision == "COUNTER_OFFER" or decision == "APPROVE", the pipeline currently either halts or disburses immediately with no user interaction gate.

Target Behavior
Intake → KYC → Underwriting
                    │
          ┌─────────┴──────────┐
          │                    │
       APPROVE            COUNTER_OFFER
          │                    │
   Show Terms UI     Show 2–3 Offer Options UI
          │                    │
   User Confirms         User Selects One
          │                    │
          └─────────┬──────────┘
                    │
              Disbursement

1. Data Model Changes
1.1 New Pydantic Models (add to models.py or inline in routes.py)
pythonclass CounterOfferOption(BaseModel):
    offer_id: str                  # e.g. "offer_1", "offer_2", "offer_3"
    principal_amount: float        # Approved loan amount for this option
    tenure_months: int             # Repayment period
    interest_rate: float           # Annual interest rate (%)
    monthly_emi: float             # Calculated EMI
    label: str                     # Human-readable label e.g. "Lower EMI Option"

class ResumeWithOfferRequest(BaseModel):
    application_id: str
    selected_offer_id: str         # Must match one of the offer_ids returned earlier

class ConfirmApprovalRequest(BaseModel):
    application_id: str
    accepted: bool                 # Must be True to proceed; False = user declined
1.2 Application State Store
Add an in-memory state store (or plug into your existing DB/cache) to hold pipeline state between the pause and resume steps.
python# In a new file: src/store/pipeline_state_store.py

from typing import Dict, Any

_store: Dict[str, Dict[str, Any]] = {}

def save_state(application_id: str, state: Dict[str, Any]) -> None:
    _store[application_id] = state

def get_state(application_id: str) -> Dict[str, Any] | None:
    return _store.get(application_id)

def clear_state(application_id: str) -> None:
    _store.pop(application_id, None)

Note for production: Replace _store with Redis or your database. The interface (save/get/clear) stays the same.


2. Underwriting Response Contract
The map_to_underwriting / decisioning agent must return the following shape. Confirm this matches your decisioning agent's actual response — if not, the mapper layer must normalize it.
json{
  "decision": "COUNTER_OFFER",
  "application_id": "app_123",
  "approved_amount": 75000.0,
  "approved_tenure_months": 36,
  "interest_rate": 11.5,
  "counter_offer_options": [
    {
      "offer_id": "offer_1",
      "principal_amount": 75000.0,
      "tenure_months": 36,
      "interest_rate": 11.5,
      "monthly_emi": 2463.0,
      "label": "Recommended"
    },
    {
      "offer_id": "offer_2",
      "principal_amount": 60000.0,
      "tenure_months": 24,
      "interest_rate": 11.0,
      "monthly_emi": 2789.0,
      "label": "Lower Principal"
    },
    {
      "offer_id": "offer_3",
      "principal_amount": 75000.0,
      "tenure_months": 48,
      "interest_rate": 12.0,
      "monthly_emi": 1975.0,
      "label": "Lower EMI"
    }
  ]
}
For APPROVE, the response must include:
json{
  "decision": "APPROVE",
  "application_id": "app_123",
  "approved_amount": 100000.0,
  "approved_tenure_months": 36,
  "interest_rate": 10.5,
  "monthly_emi": 3260.0,
  "processing_fee": 1000.0,
  "terms_summary": "Loan of ₹1,00,000 at 10.5% p.a. for 36 months. EMI: ₹3,260/month."
}

If the decisioning agent does not currently return counter_offer_options, generate them in PipelineService using the approved amount, rate, and tenure as the base, and derive 2 variants (e.g., shorter tenure + higher EMI, longer tenure + lower EMI).


3. Pipeline Service Changes (pipeline_service.py)
3.1 Split execute_full_pipeline into phases
Rename the existing method and add two new resume methods:
pythonasync def execute_until_decision(
    self, application_id: str, raw_application: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Runs KYC + Underwriting. Stops before Disbursement.
    Saves underwriting output to state store.
    Returns a response that tells the frontend what user action is needed.
    """

async def resume_after_counter_offer_selection(
    self, application_id: str, selected_offer_id: str
) -> Dict[str, Any]:
    """
    Loads saved underwriting state.
    Validates selected_offer_id exists in the saved options.
    Calls map_decisioning_to_disbursement with the selected offer data.
    Calls the disbursement agent.
    Clears state.
    Returns disbursement receipt.
    """

async def resume_after_approval_confirmation(
    self, application_id: str
) -> Dict[str, Any]:
    """
    Loads saved underwriting state.
    Calls map_decisioning_to_disbursement with the approved terms.
    Calls the disbursement agent.
    Clears state.
    Returns disbursement receipt.
    """
3.2 execute_until_decision logic (pseudocode)
python# ... (KYC steps remain unchanged) ...

# After KYC passes, run underwriting (unchanged)
uw_data = await underwriting_call(...)

decision = uw_data.get("decision")

if decision == "DECLINE":
    return {"status": "DECLINED", "application_id": application_id, "underwriting_details": uw_data}

if decision == "APPROVE":
    save_state(application_id, {"phase": "AWAITING_APPROVAL_CONFIRMATION", "uw_data": uw_data})
    return {
        "status": "AWAITING_APPROVAL_CONFIRMATION",
        "application_id": application_id,
        "approved_amount": uw_data["approved_amount"],
        "approved_tenure_months": uw_data["approved_tenure_months"],
        "interest_rate": uw_data["interest_rate"],
        "monthly_emi": uw_data["monthly_emi"],
        "processing_fee": uw_data.get("processing_fee", 0),
        "terms_summary": uw_data.get("terms_summary", "")
    }

if decision == "COUNTER_OFFER":
    options = uw_data.get("counter_offer_options") or generate_counter_offer_options(uw_data)
    save_state(application_id, {"phase": "AWAITING_OFFER_SELECTION", "uw_data": uw_data, "options": options})
    return {
        "status": "COUNTER_OFFER_PENDING",
        "application_id": application_id,
        "counter_offer_options": options
    }
3.3 resume_after_counter_offer_selection logic (pseudocode)
pythonstate = get_state(application_id)

# Guard: state must exist and be in the right phase
if not state or state["phase"] != "AWAITING_OFFER_SELECTION":
    raise ValueError(f"No pending counter offer selection for application {application_id}")

options = state["options"]
selected = next((o for o in options if o["offer_id"] == selected_offer_id), None)

if not selected:
    raise ValueError(f"Invalid offer_id: {selected_offer_id}")

# Override uw_data fields with selected offer before passing to disbursement mapper
uw_data = state["uw_data"]
uw_data["approved_amount"] = selected["principal_amount"]
uw_data["approved_tenure_months"] = selected["tenure_months"]
uw_data["interest_rate"] = selected["interest_rate"]
uw_data["monthly_emi"] = selected["monthly_emi"]

disburse_payload = map_decisioning_to_disbursement(decisioning_response=uw_data)
disburse_data = await disbursement_call(disburse_payload)

clear_state(application_id)

return {"status": "DISBURSED", "application_id": application_id, "disbursement_receipt": disburse_data}
3.4 resume_after_approval_confirmation logic (pseudocode)
pythonstate = get_state(application_id)

if not state or state["phase"] != "AWAITING_APPROVAL_CONFIRMATION":
    raise ValueError(f"No pending approval confirmation for application {application_id}")

uw_data = state["uw_data"]
disburse_payload = map_decisioning_to_disbursement(decisioning_response=uw_data)
disburse_data = await disbursement_call(disburse_payload)

clear_state(application_id)

return {"status": "DISBURSED", "application_id": application_id, "disbursement_receipt": disburse_data}

4. New API Routes (routes.py)
4.1 Modify existing /trigger_pipeline
Rename the internal call to execute_until_decision. The request model and path stay the same — only the service method called changes.
python@router.post("/trigger_pipeline")
async def trigger_pipeline(request: ApplicationTriggerRequest):
    service = PipelineService()
    try:
        result = await service.execute_until_decision(
            application_id=request.application_id,
            raw_application=request.raw_application
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
4.2 New route: POST /select_counter_offer
python@router.post("/select_counter_offer")
async def select_counter_offer(request: ResumeWithOfferRequest):
    """
    Called by frontend when user selects a counter offer option.
    Triggers disbursement with the selected offer terms.
    """
    service = PipelineService()
    try:
        result = await service.resume_after_counter_offer_selection(
            application_id=request.application_id,
            selected_offer_id=request.selected_offer_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
4.3 New route: POST /confirm_approval
python@router.post("/confirm_approval")
async def confirm_approval(request: ConfirmApprovalRequest):
    """
    Called by frontend when user accepts the approved loan terms.
    If accepted=False, the application is cancelled — no disbursement.
    """
    if not request.accepted:
        return {
            "status": "CANCELLED_BY_USER",
            "application_id": request.application_id
        }

    service = PipelineService()
    try:
        result = await service.resume_after_approval_confirmation(
            application_id=request.application_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()

5. Helper: generate_counter_offer_options
Add this as a standalone utility function in pipeline_service.py or a new src/utils/offer_generator.py:
pythondef generate_counter_offer_options(uw_data: Dict[str, Any]) -> list:
    """
    Derives 3 counter offer options from base underwriting approval data.
    Used only if the decisioning agent does not return counter_offer_options itself.
    """
    base_amount = uw_data["approved_amount"]
    base_tenure = uw_data["approved_tenure_months"]
    base_rate = uw_data["interest_rate"]

    def calc_emi(principal, annual_rate, months):
        r = annual_rate / (12 * 100)
        return round(principal * r * (1 + r)**months / ((1 + r)**months - 1), 2)

    return [
        {
            "offer_id": "offer_1",
            "principal_amount": base_amount,
            "tenure_months": base_tenure,
            "interest_rate": base_rate,
            "monthly_emi": calc_emi(base_amount, base_rate, base_tenure),
            "label": "Recommended"
        },
        {
            "offer_id": "offer_2",
            "principal_amount": base_amount,
            "tenure_months": max(12, base_tenure - 12),   # Shorter tenure
            "interest_rate": base_rate,
            "monthly_emi": calc_emi(base_amount, base_rate, max(12, base_tenure - 12)),
            "label": "Pay Faster"
        },
        {
            "offer_id": "offer_3",
            "principal_amount": base_amount,
            "tenure_months": base_tenure + 12,            # Longer tenure
            "interest_rate": round(base_rate + 0.5, 2),   # Slightly higher rate
            "monthly_emi": calc_emi(base_amount, base_rate + 0.5, base_tenure + 12),
            "label": "Lower EMI"
        }
    ]

6. Error & Edge Cases to Handle
ScenarioExpected Behavior/select_counter_offer called with no saved state400 — "No pending counter offer selection for application X"/select_counter_offer called with an invalid offer_id400 — "Invalid offer_id: offer_X"/confirm_approval called with no saved state400 — "No pending approval confirmation for application X"/confirm_approval called with accepted: false200 with status: CANCELLED_BY_USER, no disbursement triggered/trigger_pipeline called again for a application_id that already has saved stateOverwrite state — re-running the pipeline is treated as a restartDisbursement agent fails after offer selectionReturn 500, do not clear state so the user can retry

7. File Change Summary
FileChange TypeSummarysrc/store/pipeline_state_store.pyCreateIn-memory key-value store for pipeline pause statesrc/utils/offer_generator.pyCreategenerate_counter_offer_options() helpersrc/services/pipeline_service.pyModifySplit into 3 methods; import and use state storesrc/routes.pyModifyUpdate /trigger_pipeline; add /select_counter_offer and /confirm_approvalsrc/models.py (or inline)Create/ModifyAdd CounterOfferOption, ResumeWithOfferRequest, ConfirmApprovalRequest