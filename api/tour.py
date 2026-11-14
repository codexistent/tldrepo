"""Produces events for tour, yielding them as they are generated

    Decides:
        - WHAT gets sent
        - WHEN its ready
"""

import asyncio

from schemas import TourEvent, CamelModel, RepoMeta, RepoOverview, TourStopEvent, TourDoneEvent
from collections.abc import AsyncGenerator

def to_ndjson_line(event: CamelModel) -> str:
    # serialize one event as a single NDJSON line
    return event.model_dump_json(by_alias=True) + "\n"

# temporary func - yields events as they come in
async def fake_tour_events(owner: str = "pallets", repo: str = "flask", sha: str = "sha") -> AsyncGenerator[str, None]:
    # fake events for testing
    events: list[CamelModel] = [
        RepoMeta(owner="pallets", repo="flask", sha="fake-sha", cached=False),
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

    for event in events:
        yield to_ndjson_line(event)
        await asyncio.sleep(0.5)