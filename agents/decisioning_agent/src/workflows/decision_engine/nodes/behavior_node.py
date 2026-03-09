"""
Behavioral Risk Engine
Payment Pattern & Charge-Off Detector
"""

import json
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node

from src.services.llm_executor import execute_llm
from src.services.behavior_model.behavior_parser import BehaviorOutput
from src.services.behavior_model.behavior_prompt import BEHAVIOR_PROMPT


@track_node("behavior_engine")
@audit_node(agent_name="decisioning_agent")
def behavior_node(state: LoanApplicationState) -> LoanApplicationState:

    behavior_output_parser = PydanticOutputParser(
        pydantic_object=BehaviorOutput
    )

    # ==================================================
    # 1️⃣ Extract Bureau Data
    # ==================================================
    raw_experian = state.get("pi_masked_experian_data")

    tradelines = raw_experian.get("tradeline", [])

    # ==================================================
    # 2️⃣ Prepare LLM Inputs
    # ==================================================
    inputs = {
        "tradelines": json.dumps(tradelines),
        "format_instructions": behavior_output_parser.get_format_instructions(),
    }

    # ==================================================
    # 3️⃣ Execute LLM via Shared Executor
    # ==================================================
    result = execute_llm(
        prompt_template=BEHAVIOR_PROMPT,
        inputs=inputs,
        parser=behavior_output_parser,
    )

    # ==================================================
    # 4️⃣ Build Node Output
    # ==================================================
    behavior_data = result.model_dump()

    behavior_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"behavior_data": behavior_data}