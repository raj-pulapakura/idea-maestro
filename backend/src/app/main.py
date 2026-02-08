from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.checkpoint import ensure_checkpoint_schema
from app.db.migrations import run_migrations
from app.routes.test import router as test_router
from app.routes.chat import router as chat_router
from app.routes.threads import router as threads_router
from app.routes.docs import router as docs_router
from app.routes.reviews import router as reviews_router


app = FastAPI(title="Idea Maestro Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    run_migrations()
    ensure_checkpoint_schema()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(test_router)
app.include_router(chat_router)
app.include_router(threads_router)
app.include_router(docs_router)
app.include_router(reviews_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
