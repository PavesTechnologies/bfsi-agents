import ast
from pathlib import Path
from .base import Finding

FORBIDDEN_IMPORTS = {
    "domain": ["services", "adapters", "workflows", "repositories"],
    "workflows": ["adapters"],
    "api": ["adapters"],
}

EXTERNAL_SDK_KEYWORDS = ["boto3", "requests", "httpx"]

def extract_imports(file_path: Path) -> list[str]:
    try:
        tree = ast.parse(file_path.read_text())
    except SyntaxError:
        return []

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.append(name.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports


def check_import_boundaries(file_path: Path) -> list[Finding]:
    findings = []
    imports = extract_imports(file_path)
    path_parts = file_path.parts

    for layer, forbidden in FORBIDDEN_IMPORTS.items():
        if layer in path_parts:
            for imp in imports:
                for bad in forbidden:
                    if imp.startswith(bad):
                        findings.append(
                            Finding(
                                rule_id="R3",
                                severity="ERROR",
                                message=f"Forbidden import '{imp}' in {layer} layer",
                                file=str(file_path),
                                suggestion=f"Remove dependency on '{bad}' from {layer}"
                            )
                        )

    if "domain" in path_parts:
        for imp in imports:
            for sdk in EXTERNAL_SDK_KEYWORDS:
                if imp.startswith(sdk):
                    findings.append(
                        Finding(
                            rule_id="R3.1",
                            severity="ERROR",
                            message=f"External SDK '{sdk}' imported in domain layer",
                            file=str(file_path),
                            suggestion="Domain layer must be pure and side-effect free"
                        )
                    )

    return findings
