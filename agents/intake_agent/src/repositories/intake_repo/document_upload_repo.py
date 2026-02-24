from src.models.models import PgsqlDocument


class LoanIntakeDAO:
    def __init__(self, db):
        self.db = db

    async def create_document(self, data: dict) -> PgsqlDocument:
        document = PgsqlDocument(**data)
        self.db.add(document)
        return document
