import subprocess
import sys
import uvicorn

def dev():
    uvicorn.run("src.main:app", reload=True, port=8001, reload_dirs=["src"])

def prod():
    uvicorn.run("src.main:app", port=8001)

def test():
    import pytest
    pytest.main(["-v", "tests/"])

def migrate():
    print("🚀 Applying migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("✅ Migrations applied successfully.")

def migration():
    if len(sys.argv) < 2:
        print("❌ Error: Migration description is required.")
        sys.exit(1)
    description = sys.argv[1]
    print(f"📦 Creating migration: {description}")
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", description], check=True)
    print("🚀 Applying migration...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("✅ Migration completed successfully.")
