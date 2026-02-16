"""
CLI entrypoint for local development.
"""

import uvicorn
import sys
import subprocess
import os

def dev():
    uvicorn.run(
        "src.main:app",
        reload=True,
        port=8000,
        reload_dirs=["src"]
    )

def prod():
    uvicorn.run(
        "src.main:app",
        port=8000,
    )

def test():
    print("Running tests...")
    import pytest

    pytest.main(["-v", "tests/"])

    print("Tests complete.")
def migration():
    """
    Run Alembic autogenerate + upgrade.
    Usage:
        poetry run migration "add user table"
    """

    # Get description from command line
    if len(sys.argv) < 2:
        print("❌ Error: Migration description is required.")
        print('Usage: poetry run migration "your description"')
        sys.exit(1)

    description = sys.argv[1]

    if not description.strip():
        print("❌ Error: Description cannot be empty.")
        sys.exit(1)

    print(f"📦 Creating migration: {description}")

    # Run alembic revision
    subprocess.run(
        [
            "alembic",
            "revision",
            "--autogenerate",
            "-m",
            description
        ],
        check=True
    )

    print("🚀 Applying migration...")

    # Run alembic upgrade
    subprocess.run(
        [
            "alembic",
            "upgrade",
            "head"
        ],
        check=True
    )

    print("✅ Migration completed successfully.")
    
def migrate():
    """
    Run Alembic upgrade to head.
    Usage:
        poetry run migrate
    """
    print("🚀 Applying migrations...")

    # Run alembic upgrade
    subprocess.run(
        [
            "alembic",
            "upgrade",
            "head"
        ],
        check=True
    )

    print("✅ Migrations applied successfully.")
    
def downgrade():
    """
    Run Alembic downgrade by one revision.
    Usage:
        poetry run downgrade
    """
    print("🚀 Downgrading database...")

    # Run alembic downgrade
    subprocess.run(
        [
            "alembic",
            "downgrade",
            "-1"
        ],
        check=True
    )

    print("✅ Database downgraded successfully.")