from typing import Any, TypedDict


class NoteState(TypedDict, total=False):

    # Input
    transcript: str
    youtube_url: str

    # Lecture settings
    language: str
    note_type: str
    diagram_level: str

    # Chunking
    chunks: list[str]
    current_chunk: int
    chunk_results: list[Any]

    # Text AI
    analysis: Any

    # Video AI
    visual_analysis: list[Any]

    # Final
    validated: bool
    final_notes: Any