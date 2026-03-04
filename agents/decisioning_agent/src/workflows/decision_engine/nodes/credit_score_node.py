"""
Credit Score Evaluation Engine
Policy-Driven, Auditable Bureau Score Interpreter
"""

from datetime import datetime
from langchain_core.output_parsers import PydanticOutputParser

from src.core.telemetry import track_node
from src.workflows.decision_state import LoanApplicationState

from src.services.llm_executor import execute_llm
from src.services.credit_score_model.credit_score_parser import CreditScoreOutput

from src.services.credit_score_model.credit_score_prompt import CREDIT_SCORE_PROMPT


@track_node("credit_score_engine")
def credit_score_node(state: LoanApplicationState) -> LoanApplicationState:

    credit_score_output_parser = PydanticOutputParser(
    pydantic_object=CreditScoreOutput
    )
    
    # ==================================================
    # 1️⃣ Extract Bureau Data
    # ==================================================
    raw_experian = state.get("pi_masked_experian_data")

    risk_model = raw_experian.get("riskModel", [])

    score = None
    if risk_model:
        score = int(risk_model[0].get("score", 0))

    # ==================================================
    # 2️⃣ Prepare LLM Inputs
    # ==================================================
    inputs = {
        "score": score,
        "format_instructions": credit_score_output_parser.get_format_instructions(),
    }

    # ==================================================
    # 3️⃣ Execute LLM via Shared Executor
    # ==================================================
    result = execute_llm(
        prompt_template=CREDIT_SCORE_PROMPT,
        inputs=inputs,
        parser=credit_score_output_parser,
    )

    # ==================================================
    # 4️⃣ Build Node Output
    # ==================================================
    credit_score_data = result.model_dump()

    credit_score_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {"credit_score_data": credit_score_data}