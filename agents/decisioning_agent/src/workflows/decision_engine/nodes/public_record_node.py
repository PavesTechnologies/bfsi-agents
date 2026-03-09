"""
Public Record Evaluation Engine
Bankruptcy / Liens / Hard Stop Detector
"""

import json
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node

from src.services.llm_executor import execute_llm
from src.services.public_record_model.public_record_parser import PublicRecordOutput
from src.services.public_record_model.public_record_prompt import PUBLIC_RECORD_PROMPT


@track_node("public_record_engine")
@audit_node(agent_name="decisioning_agent")
def public_record_node(state: LoanApplicationState) -> LoanApplicationState:

    public_record_output_parser = PydanticOutputParser(
        pydantic_object=PublicRecordOutput
    )

    # ==================================================
    # 1️⃣ Extract Bureau Data
    # ==================================================
    raw_experian = state.get("pi_masked_experian_data")

    public_records = raw_experian.get("publicRecord", [])

    # ==================================================
    # 2️⃣ Prepare LLM Inputs
    # ==================================================
    inputs = {
        "public_records": json.dumps(public_records),
        "format_instructions": public_record_output_parser.get_format_instructions(),
    }

    # ==================================================
    # 3️⃣ Execute LLM via Shared Executor
    # ==================================================
    result = execute_llm(
        prompt_template=PUBLIC_RECORD_PROMPT,
        inputs=inputs,
        parser=public_record_output_parser,
    )

    # ==================================================
    # 4️⃣ Build Node Output
    # ==================================================
    public_record_data = result.model_dump()

    public_record_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"public_record_data": public_record_data}