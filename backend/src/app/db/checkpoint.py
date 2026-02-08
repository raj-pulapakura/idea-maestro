from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from langgraph.checkpoint.postgres import PostgresSaver

from app.db.URL import DB_URL


def checkpoint_db_url() -> str:
    if not DB_URL:
        raise RuntimeError("DATABASE_URL is required")

    parsed = urlparse(DB_URL)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    params.setdefault("sslmode", "disable")
    query = urlencode(params)
    return urlunparse(parsed._replace(query=query))


def ensure_checkpoint_schema() -> None:
    with PostgresSaver.from_conn_string(checkpoint_db_url()) as checkpointer:
        checkpointer.setup()
