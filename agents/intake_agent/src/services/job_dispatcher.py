from collections.abc import Awaitable, Callable

from src.models.job import Job
from src.services.intake_processor import process_intake

JobHandler = Callable[[Job], Awaitable[None]]

#  Map job types to their respective handlers
job_dispatcher: dict[str, JobHandler] = {
    # down the line may be replaced with `run_intake_langgraph_pipeline`
    "intake": process_intake,
}
