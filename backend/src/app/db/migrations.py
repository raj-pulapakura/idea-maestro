from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.db.get_conn_factory import conn_factory


@dataclass(frozen=True)
class MigrationFile:
    name: str
    sql: str


def _migration_dir() -> Path:
    return Path(__file__).resolve().parent / "migrations"


def _load_migrations() -> list[MigrationFile]:
    files = sorted(_migration_dir().glob("*.sql"))
    migrations: list[MigrationFile] = []
    for path in files:
        migrations.append(MigrationFile(name=path.name, sql=path.read_text(encoding="utf-8")))
    return migrations


def _ensure_schema_migrations_table() -> None:
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                  name TEXT PRIMARY KEY,
                  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        conn.commit()


def _applied_migrations() -> set[str]:
    with conn_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM schema_migrations")
            rows = cur.fetchall()
    return {row[0] for row in rows}


def _apply_migration(name: str, sql: str) -> None:
    with conn_factory() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (name,))


def run_migrations() -> None:
    _ensure_schema_migrations_table()
    applied = _applied_migrations()

    for migration in _load_migrations():
        if migration.name in applied:
            continue
        _apply_migration(migration.name, migration.sql)
