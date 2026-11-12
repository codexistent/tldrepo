import re # regex
import httpx

from fastapi import HTTPException

from dataclasses import dataclass

# dataclasses
@dataclass 
class RepoFile:
    path: str 
    size: int

@dataclass
class Snapshot:
    owner: str 
    repo: str 
    sha: str 
    files: list[RepoFile]
    truncated: bool

NAME_REGEX = re.compile(r"[A-Za-z0-9_.-]+")

# parses pasted repo url for owner and repo name
def parse_repo_url(url: str) -> tuple[str, str]:
    url = url.strip()

    for prefix in ("https://", "http://", "www.", "github.com"):
        url = url.removeprefix(prefix)

    parts = [part for part in url.split("/") if part != ""]

    if(len(parts) < 2):
        raise ValueError("Invalid url: incorrect number of parsed parts")

    owner = parts[0]
    repo = parts[1].removesuffix(".git")

    # regex check
    for name in (owner, repo):
        if(not NAME_REGEX.fullmatch(name) or name in {"..", "..."}):
            raise ValueError(f"Invalid url: {name} is not valid")

    return owner, repo

# get snapshot of data 
async def get_snapshot(client: httpx.AsyncClient, owner: str, repo: str) -> Snapshot:
    # three api calls in a sequence: branch, SHA, tree
    
    # get default branch 
    response = await github_get(client, f"/repos/{owner}/{repo}")
    default_branch = response["default_branch"]

    # get SHA so we always get repo at same version/time 
    response = await github_get(client, f"/repos/{owner}/{repo}/commits/{default_branch}")
    repo_sha = response["sha"]

    # get file structure of repo
    tree = await github_get(client, f"/repos/{owner}/{repo}/git/trees/{repo_sha}", params={"recursive": "1"})

    files = [RepoFile(path=entry["path"], size=entry.get("size", 0)) for entry in tree["tree"] if entry["type"] == "blob"]

    return Snapshot(
        owner = owner,
        repo = repo,
        sha = repo_sha, 
        files = files, 
        truncated = tree.get("truncated", False)
    )

    
# get json dict of github api link
async def github_get(client: httpx.AsyncClient, path: str, params: dict | None = None) -> dict :
    response = await client.get(path, params=params)

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Repo not found or private")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="GitHub error")

    return response.json()
    