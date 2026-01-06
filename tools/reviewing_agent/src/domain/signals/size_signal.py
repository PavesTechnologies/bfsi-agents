import ast
from pathlib import Path
from .models import Signal


MAX_FUNC_SIZE = {
    "domain": 20,
    "services": 30,
    "workflows": 40,
}


def detect_large_functions(file_path: Path) -> list[Signal]:
    try:
        # tree = ast.parse(file_path.read_text())
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)

    except SyntaxError:
        return []

    path = file_path.as_posix()
    layer = (
        "domain" if "/src/domain/" in path else
        "services" if "/src/services/" in path else
        "workflows" if "/src/workflows/" in path else
        None
    )

    if not layer:
        return []

    max_size = MAX_FUNC_SIZE[layer]
    signals = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not node.body:
                continue

            start = node.lineno
            end = max(getattr(n, "lineno", start) for n in ast.walk(node))
            size = end - start + 1

            if size > max_size:
                signals.append(
                    Signal(
                        type="LARGE_FUNCTION",
                        file=path,
                        function=node.name,
                        line=node.lineno,
                        score=1,
                        reason=f"Function '{node.name}' is {size} LOC (>{max_size})",
                    )
                )

    return signals