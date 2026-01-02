import ast
from pathlib import Path
from .base import Finding

FORBIDDEN_IMPORTS = {
    "domain": ["services", "adapters", "workflows", "repositories"],
    "workflows": ["adapters"],
    "api": ["adapters"],
}

EXTERNAL_SDK_KEYWORDS = ["boto3", "requests", "httpx"]


def detect_layer(file_path: Path) -> str | None:
    path = file_path.as_posix()

    if "/src/domain/" in path:
        return "domain"
    if "/src/workflows/" in path:
        return "workflows"
    if "/src/api/" in path:
        return "api"

    return None


def extract_imports(file_path: Path) -> list[tuple[str, int]]:
    try:
        tree = ast.parse(file_path.read_text())
    except SyntaxError:
        return []

    imports: list[tuple[str, int]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.append((name.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.module, node.lineno))

    return imports


def check_import_boundaries(file_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    imports = extract_imports(file_path)
    layer = detect_layer(file_path)

    if not layer:
        return findings

    forbidden = FORBIDDEN_IMPORTS.get(layer, [])

    for imp, line in imports:
        for bad in forbidden:
            if f".{bad}" in f".{imp}":
                findings.append(
                    Finding(
                        rule_id="R3",
                        severity="ERROR",
                        message=f"Forbidden import '{imp}' in {layer} layer",
                        file=str(file_path),
                        line=line,
                        suggestion=f"Remove dependency on '{bad}' from {layer}",
                    )
                )
                break  # avoid duplicate findings for same import

    if layer == "domain":
        for imp, line in imports:
            for sdk in EXTERNAL_SDK_KEYWORDS:
                if imp == sdk or f".{sdk}" in f".{imp}":
                    findings.append(
                        Finding(
                            rule_id="R3.1",
                            severity="ERROR",
                            message=f"External SDK '{sdk}' imported in domain layer",
                            file=str(file_path),
                            line=line,
                            suggestion="Domain layer must be pure and side-effect free",
                        )
                    )
                    break

    return findings
