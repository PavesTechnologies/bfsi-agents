import json
import os
from pathlib import Path

os.environ.setdefault("DATABASE_GENERIC", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("SERVICE_NAME", "decisioning_agent")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://test:test@localhost:5432/testdb")

from src.services.validation.release_artifact_writer import write_release_evidence_bundle


def test_release_artifact_export_writes_file(tmp_path):
    output_path = write_release_evidence_bundle(
        output_dir=str(tmp_path),
        validation_summary={"tests_passed": 5},
        monitoring_summary={"alert_count": 0},
        sample_outputs={"approve": {"decision": "APPROVE"}},
        filename_prefix="integration_release",
    )

    path = Path(output_path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path.exists()
    assert payload["validation_summary"]["tests_passed"] == 5
