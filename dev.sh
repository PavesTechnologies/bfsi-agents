#!/usr/bin/env bash
# Convenience wrapper — delegates to dev.ps1 on Windows.
# Run from repo root: bash dev.sh
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
powershell.exe -ExecutionPolicy Bypass -File "$(cygpath -w "$REPO_ROOT/dev.ps1" 2>/dev/null || echo "$REPO_ROOT/dev.ps1")"
