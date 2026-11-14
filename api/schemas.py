from typing import Literal, Annotated

from pydantic import BaseModel, ConfigDict, TypeAdapter, Field
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    model_config=ConfigDict(alias_generator=to_camel, populate_by_name=True) # # snake case to camel case

class FileMeta(CamelModel):
    type: Literal["meta"] = "meta"
    owner: str
    repo: str
    sha: str 
    cached: bool = False

class RepoOverview(CamelModel):
    type: Literal["overview"] = "overview"
    summary: str 
    stack: list[str] # = Field(max_length = 6)
    entry_point: str 

# a stop along the tour to explore a specific file; cld be better named lol
class TourStopEvent(CamelModel):
    type: Literal["stop"] = "stop"
    index: int = Field(ge=1)
    title: str # = Field(max_length = 60)
    path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    explanation: str # = Field(max_length = 250)
    why_it_matters: str # = Field(max_length = 125)

class TourDoneEvent(CamelModel):
    type: Literal["done"] = "done"
    stop_count: int 
    ms: int

class TourErrorEvent(CamelModel):
    type: Literal["error"] = "error"
    message: str

class TourRequest(CamelModel):
    request_url: str

TourEvent = Annotated[
    FileMeta | RepoOverview | TourStopEvent | TourDoneEvent | TourErrorEvent,
    Field(discriminator = "type")
]
tour_event_adapter = TypeAdapter(TourEvent)