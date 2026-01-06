from pathlib import Path

from adapters.git_adapter import get_first_changed_line
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
            line = get_first_changed_line(str(file_path)) or 1
            return [
                Signal(
                    type="SENSITIVE_LAYER",
                    file=path,
                    function=None,
                    line=line,
                    score=1,
                    reason=f"Change in sensitive layer ({layer.strip('/')})",
                )
            ]
    return []
