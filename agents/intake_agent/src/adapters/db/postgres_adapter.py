import os
from psycopg import connect
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()


class PostgresAdapter:
    _connection = None

    @classmethod
    def get_connection(cls):
        if cls._connection is None:
            cls._connection = connect(
                host=os.getenv("POSTGRES_HOST"),
                port=os.getenv("POSTGRES_PORT"),
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                sslmode=os.getenv("POSTGRES_SSLMODE", "require"),
                row_factory=dict_row,
            )
        return cls._connection
