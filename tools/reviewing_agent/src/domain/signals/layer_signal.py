from pathlib import Path
from .models import Signal

SENSITIVE_LAYERS = [
    "/src/domain/",
    "/src/services/",
    "/src/workflows/",
]

def detect_sensitive_layer(file_path: Path) -> list[Signal]:
    path = file_path.as_posix()
    for layer in SENSITIVE_LAYERS:
        if layer in path:
            return [
                Signal(
                    type="SENSITIVE_LAYER",
                    file=path,
                    function=None,
                    score=1,
                    reason=f"Change in sensitive layer ({layer.strip('/')})",
                )
            ]
    return []
