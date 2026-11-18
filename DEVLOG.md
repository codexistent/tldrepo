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

## First Run

To run it all up, we ran:

- `cd api`, `pip install -r requirements.txt` (for mac it's `pip3`)
  - if the wheel errors do `pip install -r requirements.txt --only-binary cryptography`
- started frontend in new terminal: `cd web`, `npm run dev`
- started backend in new terminal: `cd api`, `uvicorn main:app --reload`

We're now up and running! The API health check worked so we'll next deploy our app.

## Contracts

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

## GitHub API

In `fetch-gh` branch we implemented the code for fetching and processing the data collected via GitHub API.

Using the public `pallets/flask` repo as mock data, we mapped out which fields we'd need:

- `default_branch` from `https://api.github.com/repos/pallets/flask`
- top level `sha` from `https://api.github.com/repos/pallets/flask/commits/main`
- `tree` array in `https://api.github.com/repos/pallets/flask/git/trees/%3Cthat%20sha%3E?recursive=1`
- `https://raw.githubusercontent.com/pallets/flask/%3Csha%3E/README.md`

## `pick_key_files`

One of the most algorithm/consideration-heavy parts of our application is in how we choose to pick which files to display or take into account as being key on the tour.

As of our current implementation, we use a deterministic algorithm which cycles through a repo's files and assigns point scores based on attributes of a file. For instance:

- if `README` at root, +100
- if file name in `MANIFESTS` (a constant list), +80
- lower depths receive +20; higher depths +10
  and so on.

In the future we can use a more flexible non-deterministic algorithm, such as by plugging in an AI API, but without good architecture work this would only slow our app so we will go with deterministic for now.

## Fetching files

Implementing the process of actually fetching text from our desired urls was interesting too. However, a key point I'd like to note is the process in which we managed the calls to all the interesting files we want to read the text from (and thus use to determine the info and stops covered for the tour).

Specifically, the workflow went as follows:

- For each of the files we've picked, call the async function `fetch_file(path)` (which fetches the top ~250ish lines of a file with `path`) _without_ `await`
  - What then happens is a coroutine object is returned (essentially a paused task that hasn't started yet, and which can be started later)
- Call `asyncio.gather(*coroutines)` to run all the queued coroutines concurrently, returning the list of results in the same order they were established in
- In `fetch_file`, all queries to github required reserving a semaphore first, so only 8 simultaneous requests can be sent to github at once
  - A semaphore is an object which helps control how many threads can access a shared resource at the same time. Only a certain number of reservations can be made on a semaphore before some must be released first for others to reserve it (think of it as a room with a fixed number of chairs, so only that no. of ppl can sit in them at any time)

# 11/13/2026

After wrapping up work with the GitHub API yesterday, we now move on to wiring our front and back ends so that they receive streamed data.

The mental model is that we write a generator which yields pieces of the full output as they come in, and FastAPI sends each piece to frontend the moment it's yielded. We'll use NDJSON instead of JSON for this.

## Streaming - backend

### Streaming data w/ `yield` and `AsyncGenerator`

We started out by building a mock/testing function, `fake_tour_events`, plugged in some AI-generated mock data:

```json
events: list[CamelModel] = [
    FileMeta(owner="pallets", repo="flask", sha="fake-sha", cached=False),
    RepoOverview(
        summary="Flask is a lightweight web framework for Python.",
        stack=["Python", "Werkzeug", "Jinja"],
        entry_point="src/flask/app.py",
    ),
    TourStopEvent(
        index=1,
        title="The application object",
        path="src/flask/app.py",
        start_line=1,
        end_line=40,
        explanation="Defines the Flask class that every app is built on.",
        why_it_matters="Everything else plugs into this object.",
    ),
    TourStopEvent(
        index=2,
        title="Routing helpers",
        path="src/flask/helpers.py",
        start_line=10,
        end_line=30,
        explanation="Utility functions used across request handling.",
        why_it_matters="You'll see these called from almost every route.",
    ),
    TourDoneEvent(stop_count=2, ms=2000),
]
```

and tested by executing

```
curl.exe -N -X POST http://localhost:8000/api/tours -H "Content-Type: application/json" -d "@body.json"
```

### Building the prompt

Since we only ever send one prompt to Gemini per repo, building the prompt we send to it is a big deal for our app.

The function `build_prompt` builds the prompt in `tour.py`. It builds off of `format_tree` and `format_file`, which build out the string listing all the paths of a repo and a file of a repo (with numbered lines) respectively. Then `build_prompt` pieces together the full string; for this function's main string (the list `sections` which then gets strung together), we used AI to help refine our prompt.

We added a debugging route `/debug/bp` to test that the prompt building was working.

# 11/17/2026

Whale there was the AMCs but now we're back to building.

## Streaming - backend (contd.)

### Raw gemini streaming

Created an async streaming client object for `create_tour`. Tested with curl:

```
curl.exe -N -X POST http://localhost:8000/api/tours -H "Content-Type: application/json" -d "@body-real.json"
{"type":"meta","owner":"pallets","repo":"flask","sha":"49943b5a94413a530761350f04e896f76e8d620e","cached":false}
{"type":"done","stopCount":2,"ms":9709}
```

which returned the following response via fastAPI (the number represents the second of which the response chunk was returned):

```
6151.967599987984 '{"type":"overview","summary":"Flask is a lightweight'
6187.968600017484 ' WSGI web framework for Python, designed for flexibility and scalability. It provides the core application object and routing, while allowing developers to choose'
6258.792500011623 ' their own extensions and tools. This repository contains the framework source code, tests, and example applications.","stack":["Python'
6289.864599995781 '","WSGI","Werkzeug","Jinja","Click","Pallets"],"entryPoint":"src/flask/app.py"}\n{"'
6313.900500012096 'type":"stop","index":1,"title":"Introduction to the Flask Framework","path":"README.md","startLine'
6372.8539000148885 '":1,"endLine":40,"explanation":"This file provides a high-level overview of Flask, its design philosophy, and'
6436.484100006055 ' a quick \\"Hello, World!\\" example to get started. It links to documentation and explains how to contribute to the project.","whyIt'
6481.019400001969 'Matters":"It is the first point of contact for understanding the project\'s purpose and getting up and running."}'
6525.006100011524 '\n{"type":"stop","index":2,"title":"Project Configuration and Dependencies","path":"pyproject.toml","startLine":1,"'
6587.221199995838 'endLine":30,"explanation":"This file defines the project metadata, build system, and core dependencies like Werkzeug'
6621.8893000041135 ' and Jinja. It also configures development tools like ruff, mypy, and tox for testing and linting.","whyItMat'
6680.630599963479 'ters":"It manages the environment, dependencies, and CI/CD tooling required for development."}\n{"type":"stop","index":3,"'
6722.848800010979 'title":"The Public API Surface","path":"src/flask/__init__.py","startLine":1,"endLine'
6781.628399970941 '":39,"explanation":"This file exposes the primary classes and functions that users import when using Flask, such as Flask'
6818.659899989143 ", Blueprint, request, and render_template. It acts as the main entry point for the library's public interface"
6896.173099987209 '.","whyItMatters":"It defines what users see and interact with when they import the flask package."}\n'
6914.500699960627 '{"type":"stop","index":4,"title":"The Core Flask Application Class","path":"src/flask/app'
6936.974999960512 '.py","startLine":108,"endLine":140,"explanation":"This is the heart of'
7016.6376999695785 ' the framework, where the Flask class is defined. It manages the application lifecycle, configuration, and acts as the central registry'
7053.533300000709 ' for routes and view functions.","whyItMatters":"This class is the foundation of every Flask application."}\n'
7073.449799965601 '{"type":"stop","index":5,"title":"Command Line Interface Logic","path":"src/flask/cli.'
7134.938500006683 'py","startLine":37,"endLine":76,"explanation":"This module handles the logic for discovering and loading the Flask'
7172.726099961437 ' application from the command line. It includes utilities for finding the app instance or factory function in a module.","whyIt'
7215.263699996285 'Matters":"It enables the flask run command and other CLI interactions essential for development."}\n{"type":"stop","'
7284.90560001228 'index":6,"title":"JSON Serialization Utilities","path":"src/flask/json/__init__.py","startLine'
7324.85530001577 '":13,"endLine":45,"explanation":"This module provides helpers for serializing and deserializing JSON data'
7340.087299991865 '. It integrates with the application context to allow custom JSON providers, ensuring consistent behavior across the app.","whyItMat'
7400.9057999937795 'ters":"It simplifies handling JSON requests and responses, a common task in modern web development."}\n{"type":"stop'
7445.185299962759 '","index":7,"title":"Practical Application Example","path":"examples/tutorial/flaskr/__init__.py","'
7478.718400001526 'startLine":1,"endLine":40,"explanation":"This file demonstrates how to structure a real-world Flask'
7526.1785999755375 ' application using the factory pattern. It shows how to configure the app, register blueprints, and initialize database extensions.","why'
7576.607699971646 'ItMatters":"It serves as a best-practice template for building scalable, modular Flask applications."}'
```

Here we had to switch out the `gemini-3.8-flash` model with `gemini-3.1-flash-lite` because we were getting 503 error even after it did its automated retries.
