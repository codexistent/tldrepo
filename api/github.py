import re # regex

# parses pasted repo url for owner and repo name
def parse_repo_url(url: str):
    url = url.strip()
    url = url.removeprefix("www.").removeprefix("https://").removeprefix("http://").removeprefix("github.com")

    parts = url.removeprefix("/").split("/")

    if(len(parts) != 2):
        raise ValueError("Invalid url: incorrect number of parsed parts")

    owner = parts[0]
    repo = parts[1].removesuffix(".git")

    # regex check
    if(not re.fullmatch(r"[A-Za-z0-9_.-]", owner)):
        raise ValueError("Invalid url: could not parse owner")
    if(not re.fullmatch(r"[A-Za-z0-9_.-]", repo)):
        raise ValueError("Invalid url: could not parse repo")

    