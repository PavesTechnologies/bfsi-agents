"""
Debt Exposure Engine
Outstanding Liability Evaluator
"""

import json
from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState

from src.services.llm_executor import execute_llm
from src.services.exposure_model.exposure_parser import ExposureOutput
from src.services.exposure_model.exposure_prompt import EXPOSURE_PROMPT


@track_node("exposure_engine")
def exposure_node(state: LoanApplicationState) -> LoanApplicationState:

    exposure_output_parser = PydanticOutputParser(
        pydantic_object=ExposureOutput
    )

    # ==================================================
    # 1️⃣ Extract Bureau Data
    # ==================================================
    raw_experian = state.get("pi_masked_experian_data")

    tradelines = raw_experian.get("tradeline", [])

    # Filter open trades only
    open_trades = [
        t for t in tradelines if t.get("openOrClosed") == "O"
    ]

    # ==================================================
    # 2️⃣ Prepare LLM Inputs
    # ==================================================
    inputs = {
        "all_trades": json.dumps(open_trades),
        "format_instructions": exposure_output_parser.get_format_instructions(),
    }

    # ==================================================
    # 3️⃣ Execute LLM via Shared Executor
    # ==================================================
    result = execute_llm(
        prompt_template=EXPOSURE_PROMPT,
        inputs=inputs,
        parser=exposure_output_parser,
    )

    # ==================================================
    # 4️⃣ Build Node Output
    # ==================================================
    exposure_data = result.model_dump()

    exposure_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"exposure_data": exposure_data}