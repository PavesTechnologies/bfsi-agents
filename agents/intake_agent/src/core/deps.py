class DatabaseClient:
    def ping(self) -> bool:
        """
        Lightweight connectivity check.
        Should NOT run queries.
        """
        return True  # Stub implementation


db_client = DatabaseClient()