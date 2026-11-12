`types.ts` and `schemas.py` must stay in sync.

# Routes

| Route                         | Auth | Returns                                                                    |
| :---------------------------- | :--- | :------------------------------------------------------------------------- |
| `GET /api/health`             | no   | `{"status: "ok"}`; also used to wake backend early                         |
| `POST /api/tours`             | yes  | NDJSON stream of tour events (one JSON object per line); body: `{repoUrl}` |
| `GET /api/tours/{owner}/repo` | no   | latest saved tour (owner, repo, sha, events, createdAt) or 404             |
| `GET /api/tours/recent`       | no   | 12 most recent tours: owner, repo, stopCount, createdAt                    |

# Events/types

| type       | origin                    | fields                                                                                                                 | purpose                                                                 |
| :--------- | :------------------------ | :--------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------- |
| `meta`     | server                    | owner, repo, sha, cached (bool), fileCount                                                                             | sent first before any AI work so page reacts in moments/perceived speed |
| `overview` | gemini                    | summary (2-3 sentences), stack (up to 6 strings), entryPoint (a path)                                                  | what the repo is + how it's built                                       |
| `stop`     | gemini, checked by server | index (from 1), title (8 words max), path, startLine, endLine, explanation (50 words max), whyItMatters (25 words max) | one code/file stop on tour; references real lines                       |
| `done`     | server                    | stopCount, ms                                                                                                          | marks end w/ total time                                                 |
| `error`    | server                    | message                                                                                                                | anything that fails after streaming started                             |
