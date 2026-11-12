# 11/11/2026

11:11... what a lucky day to be starting a project!

To kick it off, the first thing I did was to scope (in `SCOPE.md`).

## Scaffolding

The first real decision I had to make was picking the linter. We used `ESLint` cuz its standard.

# 11/12/2026

## Scaffolding, contd.

I encountered my first error today, specifically when installing `shadcn` into my app:

```
✖ Validating import alias.

Could not find valid path aliases or package imports for init.
Configure path aliases in tsconfig.json or imports in package.json, then run init again.
Learn more at https://ui.shadcn.com/docs/installation/manual#configure-import-aliases.
```

This was fixed by adding the following lines to `tsconfig.json`:

```
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

We also set up browser side routing, rewriting from all paths to `/index.html`, and configured Cross-Origin Resource Sharing in `main.py` to allow frontend to read data from Python backend.

Finally, we added a venv to our `/api` directory.

Overall, our file structure turned out something like this:

```
tldrepo
  |___ web <-- frontend
  |
  |___ api <-- backend
        |___ .venv
```

# First Run

To run it all up, we ran:

- `cd api`, `pip install -r requirements.txt` (for mac it's `pip3`)
  - if the wheel errors do `pip install -r requirements.txt --only-binary cryptography`
- started frontend in new terminal: `cd web`, `npm run dev`
- started backend in new terminal: `cd api`, `uvicorn main:app --reload`

We're now up and running! The API health check worked so we'll next deploy our app.

# Contracts

The next step we took before writing logic was creating the types and API contracts our app would use. We did this first so frontend and backend can't disagree later down the line, and such that any mismatch shows up as a type or validation error instead of a blank screen.

We mapped out all types/API contracts in `CONTRACTS.md`. Now we'll implement them in the `contracts` branch.

To validate our changes were working, in `/api` we ran:

```
>>> from schemas import tour_event_adapter
>>> tour_event_adapter.validate_json('{"type": "stop", "index": 1, "title": "App entry point", "path": "src/main.py", "startLine": 1, "endLine": 20, "explanation": "Creates the app.", "whyItMatters": "Everything starts here."}')
```

and this returned:

```
TourStopEvent(type='stop', index=1, title='App entry point', path='src/main.py', start_line=1, end_line=20, explanation='Creates the app.', why_it_matters='Everything starts here.')
```

with camel case, so our pydantic adapter is working.

# GitHub API

In `fetch-gh` branch we implemented the code for fetching and processing the data collected via GitHub API.

Using the public `pallets/flask` repo as mock data, we mapped out which fields we'd need:

- `default_branch` from `https://api.github.com/repos/pallets/flask`
- top level `sha` from `https://api.github.com/repos/pallets/flask/commits/main`
- `tree` array in `https://api.github.com/repos/pallets/flask/git/trees/%3Cthat%20sha%3E?recursive=1`
- `https://raw.githubusercontent.com/pallets/flask/%3Csha%3E/README.md`
