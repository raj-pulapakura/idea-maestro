from langgraph.config import get_stream_writer

def emit_event(kind: str, payload: dict):
    writer = get_stream_writer()
    if writer:
        # This becomes a streamed "custom" chunk
        writer({"type": kind, **payload})