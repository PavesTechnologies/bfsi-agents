import subprocess
import sys
import asyncio
import json
import uvicorn

from src.core.database import AsyncSessionLocal
from src.repositories.underwriting_monitoring_snapshot_repository import (
    UnderwritingMonitoringSnapshotRepository,
)
from src.repositories.underwriting_repository import UnderwritingRepository
from src.services.monitoring.snapshot_job import run_monitoring_snapshot_job
from src.services.validation.release_artifact_writer import (
    write_release_evidence_bundle,
)

def dev():
    uvicorn.run("src.main:app", reload=True, port=8002, reload_dirs=["src"])

def prod():
    uvicorn.run("src.main:app", port=8002)

def test():
    import pytest
    pytest.main(["-v", "tests/"])

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
        ["alembic", "revision", "--autogenerate", "-m", description], check=True
    )

    print("🚀 Applying migration...")

    # Run alembic upgrade
    subprocess.run(["alembic", "upgrade", "head"], check=True)

    print("✅ Migration completed successfully.")


def migrate():
    """
    Run Alembic upgrade to head.
    Usage:
        poetry run migrate
    """
    print("🚀 Applying migrations...")

    # Run alembic upgrade
    subprocess.run(["alembic", "upgrade", "head"], check=True)

    print("✅ Migrations applied successfully.")


def downgrade():
    """
    Run Alembic downgrade by one revision.
    Usage:
        poetry run downgrade
    """
    print("🚀 Downgrading database...")

    # Run alembic downgrade
    subprocess.run(["alembic", "downgrade", "-1"], check=True)

    print("✅ Database downgraded successfully.")


def lint():
    """
    Run Ruff for linting and formatting.
    Usage:
        poetry run lint
    """
    print("Running linter (Ruff)...")

    # 1. Run the linter/checker
    check_result = subprocess.run(["ruff", "check", "src", "tests", "--fix"])

    # 2. Run the formatter
    format_result = subprocess.run(["ruff", "format", "src", "tests"])

    if check_result.returncode == 0 and format_result.returncode == 0:
        print("Linting and formatting complete. Code is clean!")
    else:
        print("Linting issues found.")
        sys.exit(1)


def run_monitoring_snapshot():
    async def _run():
        async with AsyncSessionLocal() as session:
            repo = UnderwritingRepository(session)
            snapshot_repo = UnderwritingMonitoringSnapshotRepository(session)
            result = await run_monitoring_snapshot_job(
                underwriting_repository=repo,
                snapshot_repository=snapshot_repo,
                segment_key="default_segment",
            )
            print(json.dumps(result, indent=2, default=str))

    asyncio.run(_run())


def export_release_evidence():
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "release_artifacts"
    path = write_release_evidence_bundle(
        output_dir=output_dir,
        validation_summary={"source": "cli", "status": "manual_export"},
        monitoring_summary={},
        sample_outputs={},
    )
    print(path)
