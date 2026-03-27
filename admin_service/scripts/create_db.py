"""
Creates the admin_db database on the Aiven PostgreSQL instance.

Connects to defaultdb (which always exists) and issues CREATE DATABASE.
Must be run before `alembic upgrade head`.

Usage:
    python scripts/create_db.py
"""

import sys
import os

# Add project root to path so src.core.config is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from src.core.config import get_settings

settings = get_settings()

# Parse host/port/user/password from ADMIN_DB_URL_SYNC
# Format: postgresql+psycopg2://user:pass@host:port/admin_db?sslmode=require
raw = settings.admin_db_url_sync.replace("postgresql+psycopg2://", "")
credentials, rest = raw.split("@", 1)
user, password = credentials.split(":", 1)
host_port, dbname_ssl = rest.split("/", 1)
host, port = host_port.split(":", 1)
dbname = dbname_ssl.split("?")[0]   # strip ?sslmode=require

print(f"Connecting to defaultdb on {host}:{port} as {user} ...")

conn = psycopg2.connect(
    host=host,
    port=int(port),
    user=user,
    password=password,
    dbname="defaultdb",          # connect to always-existing DB
    sslmode="require",
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

cur = conn.cursor()

# Check if DB already exists
cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
exists = cur.fetchone()

if exists:
    print(f"Database '{dbname}' already exists — skipping creation.")
else:
    cur.execute(f'CREATE DATABASE "{dbname}"')
    print(f"Database '{dbname}' created successfully.")

cur.close()
conn.close()
print("Done. You can now run: alembic upgrade head")
