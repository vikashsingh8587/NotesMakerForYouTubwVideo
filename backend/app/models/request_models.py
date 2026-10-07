from typing import Literal
from pydantic import BaseModel


class GenerateNotesRequest(BaseModel):
    url: str

    language: Literal[
        "english",
        "hinglish",
        "hindi"
    ] = "hinglish"

    note_type: Literal[
        "detailed",
        "revision",
        "exam"
    ] = "detailed"

    diagram_level: Literal[
        "auto",
        "more",
        "minimal"
    ] = "auto"


class GenerateNotesResponse(BaseModel):
    note_id: str
    notes_url: str