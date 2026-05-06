from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.env == "Development",
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Read-only connection to the decisioning_agent DB for application tracking
decisioning_engine = create_async_engine(
    settings.DECISIONING_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

DecisioningSessionLocal = async_sessionmaker(
    bind=decisioning_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
