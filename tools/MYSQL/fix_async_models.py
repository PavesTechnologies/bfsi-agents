import re
import sys
import os


def fix_relationships(file_path: str) -> None:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match relationship() calls (multiline-safe)
    pattern = r"(relationship\([^)]+)(\))"

    def add_lazy(match):
        relationship_content = match.group(1)

        # Skip if lazy already exists
        if "lazy=" in relationship_content:
            return match.group(0)

        return f'{relationship_content}, lazy="selectin"{match.group(2)}'

    fixed_content = re.sub(pattern, add_lazy, content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fixed_content)

    print(f"✅ Fixed relationships in {file_path}")


def resolve_file_path() -> str:
    """
    Behavior:
    - No argument → use default models.py (script directory)
    - Relative path → resolved from current working directory
    - Absolute path → used directly
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(script_dir, "models.py")

    # No argument → default
    if len(sys.argv) <= 1:
        return default_path

    provided_path = sys.argv[1]

    print(provided_path)
    # Resolve relative paths from where CMD is opened
    if not os.path.isabs(provided_path):
        provided_path = os.path.abspath(
            os.path.join(os.getcwd(), provided_path)
        )
    print(provided_path)
    if os.path.isfile(provided_path):
        return provided_path

    print(f"⚠️ File not found: {sys.argv[1]}")
    print("➡️ Falling back to default models.py")
    return default_path



if __name__ == "__main__":
    file_path = resolve_file_path()

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"❌ models.py not found at {file_path}")

    fix_relationships(file_path)