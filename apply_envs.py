# apply_envs.py — Apply a consolidated all.env back to individual service .env files.
#
# Usage:
#   python apply_envs.py                        # apply all.env in current dir
#   python apply_envs.py my_overrides.env       # use a custom consolidated file
#   python apply_envs.py --dry-run              # preview changes without writing
#   python apply_envs.py --base-dir <path>      # resolve service paths from a different root
#
# Workflow:
#   1. Receive all.env from a teammate (or run all_envs.py to generate it)
#   2. Run: python apply_envs.py --dry-run      (verify what will be written)
#   3. Run: python apply_envs.py                (apply)
#
# Behaviour:
#   - Each service .env is fully overwritten with the content from all.env.
#   - If a service .env does not exist, it is created (including parent directories).
#   - Target paths are read directly from the # Source: headers in all.env.

import os
import sys
import re


def parse_combined_env(combined_path):
    """Parse all.env into {relative_path: [lines]} using # Source: headers."""
    sections = {}
    current_path = None
    current_lines = []

    with open(combined_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"^# Source:\s+(.+)$", line.strip())
            if match:
                if current_path is not None:
                    sections[current_path] = current_lines
                current_path = match.group(1).strip()
                current_lines = []
            elif current_path is not None and not line.strip().startswith("# ==="):
                current_lines.append(line)

    if current_path is not None:
        sections[current_path] = current_lines

    return sections


def apply_env_file(base_dir, rel_path, lines, dry_run=False):
    target_path = os.path.join(base_dir, rel_path)
    content = "".join(lines).strip() + "\n"

    if dry_run:
        status = "[CREATE]" if not os.path.exists(target_path) else "[OVERWRITE]"
        print(f"  {status} {rel_path}")
        for line in lines:
            if line.strip():
                print(f"    {line.rstrip()}")
        return

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    status = "CREATED" if not os.path.exists(target_path) else "OVERWRITTEN"
    print(f"  [{status}] {rel_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Apply a consolidated all.env back to individual service .env files."
    )
    parser.add_argument(
        "combined_env",
        nargs="?",
        default="all.env",
        help="Path to the consolidated env file (default: all.env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files",
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Base directory to resolve relative paths from (default: current dir)",
    )
    args = parser.parse_args()

    combined_path = os.path.abspath(args.combined_env)
    base_dir = os.path.abspath(args.base_dir)

    if not os.path.exists(combined_path):
        print(f"[ERROR] Combined env file not found: {combined_path}")
        sys.exit(1)

    print(f"Reading: {combined_path}")
    print(f"Base dir: {base_dir}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}\n")

    sections = parse_combined_env(combined_path)
    if not sections:
        print("[ERROR] No sections found in combined env file.")
        sys.exit(1)

    for rel_path, lines in sections.items():
        print(f"Processing: {rel_path}")
        apply_env_file(base_dir, rel_path, lines, dry_run=args.dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
