"""
Inquiry Velocity Engine
Recent Credit Seeking Behavior Analyzer
"""

import json
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node

from src.services.llm_executor import execute_llm
from src.services.inquiry_model.inquiry_parser import InquiryOutput
from src.services.inquiry_model.inquiry_prompt import INQUIRY_PROMPT


@track_node("inquiry_engine")
@audit_node(agent_name="decisioning_agent")
def inquiry_node(state: LoanApplicationState) -> LoanApplicationState:

    inquiry_output_parser = PydanticOutputParser(
        pydantic_object=InquiryOutput
    )

    # ==================================================
    # 1️⃣ Extract Bureau Data
    # ==================================================
    raw_experian = state.get("pi_masked_experian_data")

    inquiries = raw_experian.get("inquiry", [])

    # ==================================================
    # 2️⃣ Prepare LLM Inputs
    # ==================================================
    inputs = {
        "inquiries": json.dumps(inquiries),
        "format_instructions": inquiry_output_parser.get_format_instructions(),
    }

    # ==================================================
    # 3️⃣ Execute LLM via Shared Executor
    # ==================================================
    result = execute_llm(
        prompt_template=INQUIRY_PROMPT,
        inputs=inputs,
        parser=inquiry_output_parser,
    )

    # ==================================================
    # 4️⃣ Build Node Output
    # ==================================================
    inquiry_data = result.model_dump()

    inquiry_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"inquiry_data": inquiry_data}