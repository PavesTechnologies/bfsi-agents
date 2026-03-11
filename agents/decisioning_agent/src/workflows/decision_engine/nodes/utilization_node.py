"""
Revolving Utilization Engine
Exposure Stress Analyzer
"""

import json
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState
from src.utils.audit_decorator import audit_node

from src.services.llm_executor import execute_llm
from src.services.utilization_model.utilization_parser import UtilizationOutput
from src.services.utilization_model.utilization_prompt import UTILIZATION_PROMPT


@track_node("utilization_engine")
@audit_node(agent_name="decisioning_agent")
def utilization_node(state: LoanApplicationState) -> LoanApplicationState:

    utilization_output_parser = PydanticOutputParser(
        pydantic_object=UtilizationOutput
    )

    # ==================================================
    # 1️⃣ Extract Bureau Data
    # ==================================================
    raw_experian = state.get("pi_masked_experian_data")

    tradelines = raw_experian.get("tradeline", [])

    # Filter revolving trades only
    revolving_trades = [
        t for t in tradelines if t.get("revolvingOrInstallment") == "R"
    ]

    # ==================================================
    # 2️⃣ Prepare LLM Inputs
    # ==================================================
    inputs = {
        "revolving_trades": json.dumps(revolving_trades),
        "format_instructions": utilization_output_parser.get_format_instructions(),
    }

    # ==================================================
    # 3️⃣ Execute LLM via Shared Executor
    # ==================================================
    result = execute_llm(
        prompt_template=UTILIZATION_PROMPT,
        inputs=inputs,
        parser=utilization_output_parser,
    )

    # ==================================================
    # 4️⃣ Build Node Output
    # ==================================================
    utilization_data = result.model_dump()

    utilization_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"utilization_data": utilization_data}