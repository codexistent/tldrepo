from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    model_config=ConfigDict(alias_generator=to_camel, populate_by_name=True) # # snake case to camel case

class Meta(CamelModel):
    owner: str
    repo: str
    sha: str 
    cached: bool

class Overview(CamelModel):
    summary: str 
    stack: list[str] = Field(max_length = 6)
    entry_point: str 

# a stop along the tour to explore a specific file; cld be better named lol
class Stop(CamelModel):
    index: int 
    title: str = Field(max_length = 60)
    path: str
    start_line: int 
    end_line: int 
    explanation: str = Field(max_length = 250)
    why_it_matters: str = Field(max_length = 125)

class Done(CamelModel):
    stop_count: int 
    ms: int

class Error(CamelModel):
    message: str