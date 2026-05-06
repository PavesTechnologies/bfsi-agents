"""
Creates the bank_admin database on the RDS instance if it doesn't exist.
Must be run ONCE before `poetry run migrate`.

Reads connection details from .env — connects to the `postgres` maintenance
database to issue CREATE DATABASE, then disconnects.

Usage:
    cd bank-admin-service
    poetry run python scripts/create_db.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from src.core.config import get_settings

settings = get_settings()

# Parse host/port/user/password from DATABASE_URL_SYNC
# e.g. postgresql://user:pass@host:port/dbname?sslmode=require
from urllib.parse import urlparse

parsed = urlparse(settings.DATABASE_URL_SYNC)
host     = parsed.hostname
port     = parsed.port or 5432
user     = parsed.username
password = parsed.password
dbname   = parsed.path.lstrip("/").split("?")[0]   # target DB to create
sslmode  = "require" if "ssl" in settings.DATABASE_URL_SYNC else "prefer"

print(f"Target database : {dbname}")
print(f"Host            : {host}:{port}")
print(f"User            : {user}")

# Connect to the maintenance database first
conn = psycopg2.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    dbname="postgres",       # always exists on RDS/standard Postgres
    sslmode=sslmode,
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
if cur.fetchone():
    print(f"Database '{dbname}' already exists — nothing to do.")
else:
    cur.execute(f'CREATE DATABASE "{dbname}"')
    print(f"Database '{dbname}' created successfully.")

cur.close()
conn.close()
print("Done. You can now run:  poetry run migrate")
