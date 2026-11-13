import re # regex
import httpx
import logging

import asyncio
from asyncio import Semaphore

from fastapi import HTTPException

from dataclasses import dataclass

from urllib.parse import quote

logging.basicConfig(
    level = logging.DEBUG
)

# DATACLASSES
#

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

@dataclass 
class FileContent:
    path: str
    lines: list[str]

# CONSTANTS
#

NAME_REGEX = re.compile(r"[A-Za-z0-9_.-]+")

# constants used during file selection
SKIP_DIRS = ('node_modules', 'dist', 'build', '.git', 'vendor', '__pycache__', '.next', 'coverage', '.venv', 'venv')
LOCKFILES = ('package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'cargo.lock')
MANIFESTS = ('package.json', 'pyproject.toml', 'requirements.txt', 'go.mod', 'cargo.toml', 'pom.xml')
SOURCE_EXTS = ('py', 'ts', 'tsx', 'js', 'jsx', 'go', 'rs', 'java', 'kt', 'rb', 'c', 'cpp', 'h', 'cs', 'swift', 'dart')
ENTRY_STEMS	= ('main', 'index', 'app', 'server', 'cli', '__main__', '__init__')
TEST_DIRS = ('test', 'tests', '__tests__', 'spec')
DOC_DIRS = ('docs', 'doc', 'examples')
MAX_FILES = 15
MAX_SIZE = 100_000

# constants used in to_lines 
MAX_LINES = 250 
MAX_CHARS = 12_000 
MAX_LINE_LEN = 1_000

# HELPERS
#

# get json dict of github api link
async def github_get(client: httpx.AsyncClient, path: str, params: dict | None = None) -> dict :
    try:
        response = await client.get(path, params=params)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="GitHub error")

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Repo not found or private")
    elif response.status_code in (403, 429):
        raise HTTPException(status_code=response.status_code, detail="GitHub rate limit, try again in a min")
    elif response.status_code != 200:
        raise HTTPException(status_code=502, detail="GitHub error")

    return response.json()


def score_file(parts: list[str], name: str, stem: str, suffix: str, depth: int) -> int:
    score = 0

    if(stem == "readme" and depth == 0):
        score += 100

    if(any(manifest == name for manifest in MANIFESTS)):
        score += 80

    if(any(stem == entry_stem for entry_stem in ENTRY_STEMS)):
        score += 50

    score += (depth <= 1) * 10 + (depth <= 2) * 10

    if(any(suffix == source_ext for source_ext in SOURCE_EXTS)):
        score += 10

    is_test_dir = name.startswith("test_") or ".test." in name or ".spec." in name

    for part in parts[:-1]:
        if(any(part == test_dir for test_dir in TEST_DIRS)):
            is_test_dir = True 

    score -= is_test_dir*20 

    is_doc_dir = False 

    for part in parts[:-1]:
        if(any(doc_dir == part for doc_dir in DOC_DIRS)):
            is_doc_dir = True 

    score -= is_doc_dir * 10

    return score

# determine if file should be considered for tour; returns None if not wanted and a score otherwise (greater score = greater importance)
def is_candidate(path, size) -> int | None:
    path = path.lower()
    parts = [path for path in path.split("/") if path != ""]

    name = parts[-1].lower()
    name_parts = name.rsplit(".", 1)
    stem, suffix = name_parts[0], name_parts[-1]
    depth = len(parts) - 1

    # filter out not wanted
    if(size <= 0 or size > MAX_SIZE):
        return None

    for skip in SKIP_DIRS:
        if(any(part == skip for part in parts[:-1])):
            return None
    
    if(any(parts[-1] == lockfile for lockfile in LOCKFILES)):
        return None

    if(parts[-1].endswith(".min.js")):
        return None

    # check if wanted
    if((depth == 0 and stem == "readme") or
           any(name == manifest for manifest in MANIFESTS) or
           any(suffix == src_ext for src_ext in SOURCE_EXTS)):
        return score_file(parts, name, stem, suffix, depth)

    return None

# convert text to individual lines
def to_lines(text: str) -> list[str] | None : 
    lines = text.replace("\r\n", "\n").replace("\r", "\n").removesuffix("\n").split("\n")

    if(any(len(line) > MAX_LINE_LEN for line in lines)):
        return None # minified or generated file 

    kept, chars = [], 0
    for line in lines[:MAX_LINES]:
        chars += len(line) + 1
        if(chars > MAX_CHARS):
            break
        kept.append(line)

    return kept, chars

# download one file
async def fetch_file(client: httpx.AsyncClient, semaphore: Semaphore, owner: str, repo: str, sha: str, path: str) -> FileContent | None:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{sha}/{quote(path, safe="/")}"

    # use semaphore to restrict total concurrent calls at any point in time
    async with semaphore:
        try:
            response = await client.get(url) # build full url since 
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="GitHub error") 

        # invalid status code
        if response.status_code != 200:
            return None 

        # binary file returned
        if '\x00' in response.text:
            return None

        return FileContent(path, to_lines(response.text))

# FUNCTIONS
#

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
        if(not NAME_REGEX.fullmatch(name) or name in {".", "..", "..."}):
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

# selects files to consider for tour
#   for testing: pick_key_files([RepoFile('README.md', 20), RepoFile('pyproject.toml', 500), RepoFile('src/flask/app.py', 30), RepoFile('src/flask/helpers.py', 40), RepoFile('tests/test_app.py', 20), RepoFile('docs/conf.py', 30), RepoFile('node_modules/x/index.js', 40), RepoFile('logo.png', 20), RepoFile('.gitignore', 500)])

def pick_key_files(files: list[RepoFile]) -> list[RepoFile]:
    candidate_files = []

    for file in files:
        score = is_candidate(file.path, file.size)
        if score is not None:
            candidate_files.append((file, file.size, score))

    candidate_files = sorted(candidate_files, key = lambda item: (-item[2], -item[1]))[:MAX_FILES]

    picked_files = [RepoFile(i[0].path, i[0].size) for i in candidate_files]

    logging.info(candidate_files)

    return picked_files

async def fetch_files(client: httpx.AsyncClient, snapshot: Snapshot, picked: list[RepoFile]) -> list[RepoFile]:
    # cap at 8 simultaneous gh calls
    sem = asyncio.Semaphore(8)

    coroutines = []

    for file in picked:
        coroutines.append(fetch_file(client, sem, snapshot.owner, snapshot.repo, snapshot.sha, file.path))

    files = await asyncio.gather(*coroutines)
    files = (file for file in files if file != None)

    return files
