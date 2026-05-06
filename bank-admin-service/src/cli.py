import subprocess
import sys


def dev():
    subprocess.run(["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"], check=True)


def prod():
    subprocess.run(["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005", "--workers", "2"], check=True)


def migrate():
    subprocess.run(["alembic", "upgrade", "head"], check=True)


def migration():
    msg = sys.argv[1] if len(sys.argv) > 1 else "auto_migration"
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", msg], check=True)


def create_db():
    subprocess.run([sys.executable, "scripts/create_db.py"], check=True)
