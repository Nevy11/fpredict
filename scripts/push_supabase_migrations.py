#!/usr/bin/env python3
"""Apply supabase/migrations/*.sql to the remote Supabase Postgres database."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()

PROJECT_REF = os.getenv("SUPABASE_PROJECT_ID", "agojvvfjajkkpqohehcm")
DB_HOST = os.getenv("SUPABASE_DB_HOST", f"db.{PROJECT_REF}.supabase.co")
DB_NAME = os.getenv("SUPABASE_DB_NAME", "postgres")
DB_USER = os.getenv("SUPABASE_DB_USER", "postgres")
DB_PASS = os.getenv("SUPABASE_DB_PASSWORD", os.getenv("DB_PASSWORD", ""))
DB_PORT = os.getenv("SUPABASE_DB_PORT", "5432")

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"


def apply_migrations() -> None:
    if not DB_PASS:
        raise SystemExit("Set SUPABASE_DB_PASSWORD or DB_PASSWORD in .env")

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        raise SystemExit(f"No migration files found in {MIGRATIONS_DIR}")

    print(f"Connecting to {DB_HOST} ...")
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        connect_timeout=15,
    )
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE SCHEMA IF NOT EXISTS supabase_migrations;
            CREATE TABLE IF NOT EXISTS supabase_migrations.schema_migrations (
                version text PRIMARY KEY,
                name text,
                statements text[]
            );
            """
        )

        for path in migration_files:
            version = path.name.split("_", 1)[0]
            cur.execute(
                "SELECT 1 FROM supabase_migrations.schema_migrations WHERE version = %s",
                (version,),
            )
            if cur.fetchone():
                print(f"skip  {path.name} (already applied)")
                continue

            sql = path.read_text(encoding="utf-8")
            print(f"apply {path.name}")
            cur.execute(sql)
            cur.execute(
                """
                INSERT INTO supabase_migrations.schema_migrations (version, name)
                VALUES (%s, %s)
                ON CONFLICT (version) DO NOTHING
                """,
                (version, path.name),
            )

        cur.execute("NOTIFY pgrst, 'reload schema';")

    conn.close()
    print("Remote Supabase migrations applied successfully.")


if __name__ == "__main__":
    try:
        apply_migrations()
    except Exception as error:
        raise SystemExit(f"Migration push failed: {error}") from error
