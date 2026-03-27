import subprocess
import sys


def dev():
    subprocess.run(
        ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"],
        check=True,
    )


def prod():
    subprocess.run(
        ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005", "--workers", "2"],
        check=True,
    )


def migrate():
    subprocess.run(["alembic", "upgrade", "head"], check=True)


def setup():
    """Create admin_db on Postgres, then run migrations. Run this once before first start."""
    subprocess.run([sys.executable, "scripts/create_db.py"], check=True)
    subprocess.run(["alembic", "upgrade", "head"], check=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dev"
    {"dev": dev, "prod": prod, "migrate": migrate, "setup": setup}.get(cmd, dev)()
