export type RepoRef = { owner: string; repo: string };

// regex for filtering
const OWNER = /^[A-Za-z0-9-]+$/;
const REPO = /^[A-Za-z0-9_.-]+$/;

// accepts "owner/repo" or any github.com URL; returns null otherwise
export function parseRepo(input: string): RepoRef | null {
  const path = input
    .trim()
    .split(/[?#]/)[0]!
    .replace(/^https?:\/\//i, "")
    .replace(/^(www\.)?github\.com\//i, "");

  const [owner, rawRepo] = path.split("/");
  if (!owner || !rawRepo) return null;

  const repo = rawRepo.replace(/\.git$/i, "");
  if (!OWNER.test(owner) || !REPO.test(repo) || repo === "." || repo === "..") {
    return null;
  }
  return { owner, repo };
}
