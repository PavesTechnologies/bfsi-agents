#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
AGENTS_ROOT="${REPO_ROOT}/agents"
ORCHESTRATOR_ROOT="${REPO_ROOT}/orchestrator"

to_windows_path() {
  local path="$1"

  if command -v cygpath >/dev/null 2>&1; then
    cygpath -aw "$path"
    return
  fi

  if command -v wslpath >/dev/null 2>&1; then
    wslpath -w "$path"
    return
  fi

  if [[ "$path" =~ ^/([a-zA-Z])/(.*)$ ]]; then
    printf '%s\n' "${BASH_REMATCH[1]^}:\\${BASH_REMATCH[2]//\//\\}"
    return
  fi

  printf '%s\n' "$path"
}

launch_service() {
  local name="$1"
  local service_dir="$2"
  local windows_dir

  if [[ ! -f "${service_dir}/pyproject.toml" ]]; then
    echo "Skipping ${name}: no pyproject.toml found in ${service_dir}"
    return
  fi

  windows_dir="$(to_windows_path "$service_dir")"

  cmd.exe /c start "$name" /D "$windows_dir" powershell.exe -NoExit -Command "poetry run dev" >/dev/null 2>&1
  echo "Launched ${name}"
}

if [[ ! -d "$AGENTS_ROOT" ]]; then
  echo "Agents directory not found: ${AGENTS_ROOT}" >&2
  exit 1
fi

shopt -s nullglob
agent_dirs=("${AGENTS_ROOT}"/*)
shopt -u nullglob

for agent_dir in "${agent_dirs[@]}"; do
  [[ -d "$agent_dir" ]] || continue
  launch_service "$(basename "$agent_dir")" "$agent_dir"
done

launch_service "orchestrator" "$ORCHESTRATOR_ROOT"

echo "All available agents have been launched in separate terminals."
