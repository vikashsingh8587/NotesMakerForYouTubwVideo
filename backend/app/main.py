from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from .routes.notes import router
from .services.note_store import get_notes, get_visual_status
from .rendering.html_renderer import render_notes
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .services.note_store import (
    get_notes,
    get_visual_status,
)
from .rendering.html_renderer import render_notes
app = FastAPI(title="Video to Handwritten Notes - LangGraph")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/notes/{note_id}", response_class=HTMLResponse)
def notes_page(note_id: str):
    notes = get_notes(note_id)
    if not notes:
        return HTMLResponse("<h2>Notes not found. Backend may have restarted.</h2>", status_code=404)
    return HTMLResponse(render_notes(notes, note_id=note_id, visual_status=get_visual_status(note_id)))
@app.get("/api/notes/{note_id}/status")
def notes_status(note_id: str):
    status = get_visual_status(note_id)

    if status is None:
        return {
            "status": "not_found"
        }

    return {
        "status": status
    }