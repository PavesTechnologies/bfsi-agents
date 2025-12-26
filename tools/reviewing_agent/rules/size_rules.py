import ast
from pathlib import Path
from .base import Finding

MAX_FILE_LINES = 300
MAX_FUNCTION_LINES = 50

def check_file_size(file_path: Path) -> list[Finding]:
    findings = []
    lines = file_path.read_text().splitlines()

    if len(lines) > MAX_FILE_LINES:
        findings.append(
            Finding(
                rule_id="R5.1",
                severity="WARNING",
                message=f"File exceeds {MAX_FILE_LINES} lines ({len(lines)} lines)",
                file=str(file_path),
                suggestion="Consider splitting this file into smaller modules"
            )
        )

    return findings


def check_function_size(file_path: Path) -> list[Finding]:
    findings = []

    try:
        tree = ast.parse(file_path.read_text())
    except SyntaxError:
        return findings

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.end_lineno and node.lineno:
                length = node.end_lineno - node.lineno
                if length > MAX_FUNCTION_LINES:
                    findings.append(
                        Finding(
                            rule_id="R5.2",
                            severity="WARNING",
                            message=f"Function '{node.name}' exceeds {MAX_FUNCTION_LINES} lines",
                            file=str(file_path),
                            line=node.lineno,
                            suggestion="Refactor into smaller functions"
                        )
                    )

    return findings
