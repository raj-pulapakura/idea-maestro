from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.test import router as test_router


app = FastAPI(title="Idea Maestro Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Idea Maestro backend is running"}


# Placeholder for future chat/agent endpoint
@app.post("/api/chat")
async def chat():
    # TODO: accept a payload from the frontend, call LLM/agents, and return a response
    return {"message": "Chat endpoint placeholder"}


app.include_router(test_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
