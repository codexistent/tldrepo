import os

import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from github import parse_repo_url, get_snapshot

from dotenv import load_dotenv

load_dotenv()

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

app = FastAPI(lifespan=lifespan)

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

@app.get("/api/debug/ss")
async def debug_ss(url: str, request: Request):
    try:
        owner, repo = parse_repo_url(url)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    snapshot = await get_snapshot(request.app.state.github, owner, repo)

    return {
        "sha": snapshot.sha,
        "file_count": len(snapshot.files),
        "truncated": snapshot.truncated
    }