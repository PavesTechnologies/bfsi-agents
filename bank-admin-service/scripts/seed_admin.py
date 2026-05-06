"""
Run once after migration to create the first SUPER_ADMIN user.

Usage:
    cd bank-admin-service
    poetry run python scripts/seed_admin.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from src.core.config import get_settings
from src.models.bank_user import BankUser, BankRole
from src.core.security import hash_password

settings = get_settings()

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@bank.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123!")
ADMIN_NAME = os.getenv("ADMIN_NAME", "System Administrator")


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        # Find SUPER_ADMIN role
        role_result = await db.execute(select(BankRole).where(BankRole.name == "SUPER_ADMIN"))
        role = role_result.scalar_one_or_none()
        if not role:
            print("ERROR: Roles not seeded. Run 'poetry run migrate' first.")
            return

        # Check if admin already exists
        existing = await db.execute(select(BankUser).where(BankUser.email == ADMIN_EMAIL))
        if existing.scalar_one_or_none():
            print(f"Admin user {ADMIN_EMAIL} already exists.")
            return

        admin = BankUser(
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            full_name=ADMIN_NAME,
            role_id=role.id,
        )
        db.add(admin)
        await db.commit()
        print(f"Created SUPER_ADMIN: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("IMPORTANT: Change the password immediately after first login!")

    await engine.dispose()


asyncio.run(seed())
