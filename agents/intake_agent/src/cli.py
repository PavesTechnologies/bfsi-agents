"""
CLI entrypoint for local development.
"""

import uvicorn
import sys
import subprocess
import os

def dev():
    uvicorn.run(
        "src.main:app",
        reload=True,
        port=8000,
        reload_dirs=["src"]
    )

def prod():
    uvicorn.run(
        "src.main:app",
        port=8000,
    )

def test():
    print("Running tests...")
    import pytest

    pytest.main(["-v", "tests/"])

    print("Tests complete.")

def migration():
    """
    Run Alembic autogenerate + upgrade.
    Usage:
        poetry run migration "add user table"
    """

    # Get description from command line
    if len(sys.argv) < 2:
        print("❌ Error: Migration description is required.")
        print('Usage: poetry run migration "your description"')
        sys.exit(1)

    description = sys.argv[1]

    if not description.strip():
        print("❌ Error: Description cannot be empty.")
        sys.exit(1)

    print(f"📦 Creating migration: {description}")

    # Run alembic revision
    subprocess.run(
        [
            "alembic",
            "revision",
            "--autogenerate",
            "-m",
            description
        ],
        check=True
    )

    print("🚀 Applying migration...")

    # Run alembic upgrade
    subprocess.run(
        [
            "alembic",
            "upgrade",
            "head"
        ],
        check=True
    )

    print("✅ Migration completed successfully.")

def migrate():
    """
    Run Alembic upgrade to head.
    Usage:
        poetry run migrate
    """
    print("🚀 Applying migrations...")

    # Run alembic upgrade
    subprocess.run(
        [
            "alembic",
            "upgrade",
            "head"
        ],
        check=True
    )

    print("✅ Migrations applied successfully.")

# def migrate_new_model():
#     """
#     Register a new model file and run migration.

#     Usage:
#         poetry run migrate_new_model user
#     (expects: src/models/user.py)
#     """

#     if len(sys.argv) < 2:
#         print("❌ Error: Model file name is required.")
#         print("Usage: poetry run migrate_new_model <file_name>")
#         sys.exit(1)

#     file_name = sys.argv[1].strip()

#     if not file_name:
#         print("❌ Error: File name cannot be empty.")
#         sys.exit(1)

#     models_dir = os.path.join("src", "models")
#     model_file = f"{file_name}.py"
#     model_path = os.path.join(models_dir, model_file)

#     init_file = os.path.join(models_dir, "__init__.py")

#     # ✅ Check if file exists
#     if not os.path.exists(model_path):
#         print(f"❌ Error: {model_file} not found in {models_dir}")
#         sys.exit(1)

#     print(f"📄 Found model file: {model_file}")

#     import_line = f"from .{file_name} import *\n"

#     # ✅ Create __init__.py if missing
#     if not os.path.exists(init_file):
#         open(init_file, "w").close()

#     # ✅ Read current __init__.py
#     with open(init_file, "r", encoding="utf-8") as f:
#         content = f.read()

#     # ✅ Add import if missing
#     if import_line not in content:
#         with open(init_file, "a", encoding="utf-8") as f:
#             f.write(import_line)

#         print(f"✅ Added import to __init__.py: {import_line.strip()}")

#     else:
#         print("ℹ️ Import already exists in __init__.py")

#     # ✅ Run alembic revision
#     message = f"new table created {file_name}"

#     print(f"📦 Creating migration: {message}")

#     subprocess.run(
#         [
#             "alembic",
#             "revision",
#             "--autogenerate",
#             "-m",
#             message,
#         ],
#         check=True,
#     )

#     print("🚀 Applying migration...")

#     # ✅ Run alembic upgrade
#     subprocess.run(
#         [
#             "alembic",
#             "upgrade",
#             "head",
#         ],
#         check=True,
#     )

#     print("✅ Migration completed successfully.")