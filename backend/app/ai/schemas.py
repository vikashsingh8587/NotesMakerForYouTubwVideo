from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class DiagramNode(BaseModel):
    id: str
    label: str


class DiagramEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class Diagram(BaseModel):
    type: Literal[
        "flowchart",
        "tree",
        "graph",
        "process",
        "comparison",
        "architecture",
    ]

    title: str

    nodes: List[DiagramNode] = Field(
        default_factory=list
    )

    edges: List[DiagramEdge] = Field(
        default_factory=list
    )


# --------------------------------------------------
# Practice Question
# --------------------------------------------------

class PracticeQuestion(BaseModel):
    question: str

    given: str = ""

    approach: str = ""

    solution_steps: List[str] = Field(
        default_factory=list
    )

    final_answer: str = ""

    explanation: str = ""


# --------------------------------------------------
# Lecture Table
# --------------------------------------------------

class LectureTable(BaseModel):
    title: str = ""

    columns: List[str] = Field(
        default_factory=list
    )

    rows: List[List[str]] = Field(
        default_factory=list
    )

    explanation: str = ""


# --------------------------------------------------
# Visual Information from Video
# --------------------------------------------------

class VisualInsight(BaseModel):

    timestamp: str = ""

    type: Literal[
        "slide",
        "board",
        "diagram",
        "table",
        "formula",
        "question",
        "example",
        "image",
        "other",
    ]

    title: str = ""

    content: str = ""

    important_text: List[str] = Field(
        default_factory=list
    )


# --------------------------------------------------
# Note Section
# --------------------------------------------------

class NoteSection(BaseModel):

    title: str

    definition: str = ""

    intuition: str = ""

    explanation: str = ""

    steps: List[str] = Field(
        default_factory=list
    )

    # Main example/explanation for backward compatibility.
    example: str = ""

    # Preserve ALL distinct examples demonstrated in the lecture.
    # This is intentionally a list so multiple examples are not lost.
    examples: List[str] = Field(
        default_factory=list
    )

    formula: str = ""

    complexity: str = ""

    key_points: List[str] = Field(
        default_factory=list
    )

    common_mistakes: List[str] = Field(
        default_factory=list
    )

    exam_tips: List[str] = Field(
        default_factory=list
    )

    practice_questions: List[PracticeQuestion] = Field(
        default_factory=list
    )

    tables: List[LectureTable] = Field(
        default_factory=list
    )

    diagram: Optional[Diagram] = None


# --------------------------------------------------
# Complete Lecture Notes
# --------------------------------------------------

class LectureNotes(BaseModel):

    lecture_title: str

    overview: str

    sections: List[NoteSection] = Field(
        default_factory=list
    )

    # Visual information extracted from YouTube video
    visuals: List[VisualInsight] = Field(
        default_factory=list
    )