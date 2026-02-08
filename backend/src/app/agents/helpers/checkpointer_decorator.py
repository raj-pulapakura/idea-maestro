from fastapi import Request
from langgraph.checkpoint.postgres import PostgresSaver
from app.db.checkpoint import checkpoint_db_url

DB_URL = checkpoint_db_url()

def checkpointer_route_decorator(func):
    """
    Decorator that opens a PostgresSaver context for the duration of the request
    and attaches it to request.state.checkpointer.

    Note: The wrapper intentionally only accepts `request: Request` so FastAPI
    does not interpret extra *args/**kwargs as query parameters.
    """

    async def wrapper(request: Request):
        with PostgresSaver.from_conn_string(DB_URL) as checkpointer:
            checkpointer.setup()
            request.state.checkpointer = checkpointer
            return await func(request)

    return wrapper
