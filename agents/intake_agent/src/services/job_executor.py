from abc import ABC, abstractmethod
from src.models.job import Job


class JobExecutor(ABC):

    @abstractmethod
    async def enqueue(self, job: Job) -> None:
        ...
