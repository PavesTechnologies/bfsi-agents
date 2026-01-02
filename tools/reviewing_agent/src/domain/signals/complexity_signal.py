import ast
from pathlib import Path
from .models import Signal

COMPLEXITY_THRESHOLD = 4

def detect_complex_functions(file_path: Path) -> list[Signal]:
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)

    except SyntaxError:
        return []

    path = file_path.as_posix()
    signals = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            complexity = 0

            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                    complexity += 1

            if complexity >= COMPLEXITY_THRESHOLD:
                signals.append(
                    Signal(
                        type="HIGH_COMPLEXITY",
                        file=path,
                        function=node.name,
                        score=1,
                        reason=f"Function '{node.name}' has complexity score {complexity}",
                    )
                )

    return signals
