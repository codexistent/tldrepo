import os

import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs once at startup

    if(os.getenv("GITHUB_TOKEN") is None):
        raise RuntimeError("GITHUB_TOKEN not set.")

    token = os.getenv("GITHUB_TOKEN")

    app.state.github = httpx.AsyncClient(base_url="https://api.github.com", headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}, timeout=10)

    yield 
    # runs once at shutdown

    await app.state.github.aclose()

app = FastAPI()

# CORS middleware

## frontend URLs allowed to read responses (no trailing slashes)
FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "https://tldrepo.vercel.app"
]

## add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS, # use ["*"] to allow all public origins 
    allow_methods=["*"],
    allow_headers=["*"],
)

# health check
@app.get("/api/health")
def health():
    return {"status": "true"}