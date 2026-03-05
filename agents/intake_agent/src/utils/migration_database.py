# database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from src.core.config import get_settings

settings = get_settings()


# DATABASE_URL = "postgresql+psycopg2://avnadmin:AVNS_X0ml0E8DUSxuuhGnQZX@pg-22ef5b8a-ajaykumar.h.aivencloud.com:15549/defaultdb"


class Base(DeclarativeBase):
    pass

engine = create_engine(settings.DATABASE_URL_SYNC)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
