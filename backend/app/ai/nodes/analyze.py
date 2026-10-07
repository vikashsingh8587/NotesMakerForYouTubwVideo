import time
from langchain_core.prompts import ChatPromptTemplate
from ..schemas import LectureNotes
from ..prompts import system_prompt
from ..state import NoteState

MAX_RETRIES = 3

def make_model():
    from langchain_google_genai import ChatGoogleGenerativeAI
    from ...config import GEMINI_API_KEY, GEMINI_MODEL
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY, temperature=0.2)

def _is_temporary_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in ("503", "unavailable", "429", "resource_exhausted", "remoteprotocolerror", "server disconnected", "timed out", "timeout"))

def analyze_node(state: NoteState):
    model = make_model().with_structured_output(LectureNotes)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt(state["language"], state["note_type"], state["diagram_level"])),
        ("human", """
LECTURE CHUNK:

{transcript}

Analyze ONLY this lecture chunk.

The primary goal is COMPLETE CONTENT EXTRACTION, not summarization.

You MUST preserve every distinct:
- example demonstrated by the teacher
- solved numerical/problem
- MCQ or conceptual question
- coding/programming example
- algorithm dry run
- counterexample
- input/output example
- formula application
- comparison example
- practice question

For each one, preserve the actual values/question, approach,
meaningful solution steps, final answer, and teacher reasoning
whenever present.

If the teacher gives multiple examples of the same concept,
keep them as separate examples/problems. Do not collapse them
into one generic "example".

For actual questions/problems, use practice_questions.
For non-question demonstrations, use examples.

Do not invent missing values or steps.
Do not omit an example merely because the surrounding concept
has already been explained.

The selected note type may shorten general explanations, but it
must NOT remove lecture-given examples or problems.

Create accurate notes based only on the information present
in this chunk.
"""),
    ])
    chain = prompt | model
    for attempt in range(MAX_RETRIES):
        try:
            return {"analysis": chain.invoke({"transcript": state["transcript"]})}
        except Exception as exc:
            if not _is_temporary_error(exc) or attempt == MAX_RETRIES - 1:
                raise
            wait = 2 * (2 ** attempt)
            print(f"Text AI temporary error. Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Text analysis failed")
