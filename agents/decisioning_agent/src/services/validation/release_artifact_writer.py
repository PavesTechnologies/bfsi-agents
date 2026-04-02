"""Writers for exportable governance evidence artifacts."""

import json
from datetime import datetime, timezone
from pathlib import Path

from src.services.validation.release_evidence import build_release_evidence_bundle


def write_release_evidence_bundle(
    *,
    output_dir: str,
    validation_summary: dict,
    monitoring_summary: dict | None = None,
    sample_outputs: dict | None = None,
    filename_prefix: str = "release_evidence",
) -> str:
    bundle = build_release_evidence_bundle(
        validation_summary=validation_summary,
        monitoring_summary=monitoring_summary,
        sample_outputs=sample_outputs,
    )

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = target_dir / f"{filename_prefix}_{timestamp}.json"
    path.write_text(json.dumps(bundle, indent=2, default=str), encoding="utf-8")
    return str(path)
