from typing import Awaitable, Callable, Dict

from src.models.job import Job
from src.services.intake_processor import process_intake

JobHandler = Callable[[Job], Awaitable[None]]

#  Map job types to their respective handlers
job_dispatcher: Dict[str, JobHandler] = {
    "intake": process_intake,  # down the line may be replaced with `run_intake_langgraph_pipeline`
}
