from fastapi import APIRouter, HTTPException, BackgroundTasks

from ..models.request_models import (
    GenerateNotesRequest,
    GenerateNotesResponse,
)

from ..services.youtube_service import get_transcript

from ..services.note_store import (
    save_notes,
    get_notes,
    update_notes,
    set_visual_status,
)

from ..ai.graph import build_text_graph
from ..ai.nodes.vision import analyze_video_visuals
from ..ai.schemas import LectureNotes


router = APIRouter(
    prefix="/api/notes",
    tags=["notes"],
)


def generate_visuals_background(
    note_id: str,
    youtube_url: str,
):
    """
    Runs visual analysis in the background.

    Text notes are already available to the user.
    Visual analysis failure must never delete or break
    the already generated text notes.
    """

    try:
        print(
            f"\nStarting background visual analysis: {note_id}"
        )

        # Mark visual processing as running
        set_visual_status(
            note_id,
            "processing",
        )

        # Get already saved text notes
        current_notes = get_notes(note_id)

        if current_notes is None:
            print(
                f"Note not found for visual analysis: {note_id}"
            )

            set_visual_status(
                note_id,
                "failed",
            )

            return

        # Run visual analysis
        state = {
            "youtube_url": youtube_url,
        }

        visual_result = analyze_video_visuals(state)

        visuals = visual_result.get(
            "visual_analysis",
            [],
        )

        print(
            f"Background visual analysis completed: "
            f"{len(visuals)} visuals"
        )

        # -------------------------------------------------
        # IMPORTANT:
        # Convert visual dictionaries into VisualInsight
        # objects through full LectureNotes validation.
        # -------------------------------------------------

        updated_data = current_notes.model_dump()

        updated_data["visuals"] = visuals

        updated_notes = LectureNotes.model_validate(
            updated_data
        )

        # Save updated notes
        success = update_notes(
            note_id,
            updated_notes,
        )

        if success:
            set_visual_status(
                note_id,
                "completed",
            )

            print(
                f"Notes updated with visuals: {note_id}"
            )

        else:
            set_visual_status(
                note_id,
                "failed",
            )

            print(
                f"Failed to update notes: {note_id}"
            )

    except Exception as e:

        print(
            "BACKGROUND VISUAL ERROR:",
            repr(e),
        )

        # IMPORTANT:
        # Text notes are already saved.
        # Visual failure must NOT affect them.

        set_visual_status(
            note_id,
            "failed",
        )


@router.post(
    "/generate",
    response_model=GenerateNotesResponse,
)
def generate(
    req: GenerateNotesRequest,
    background_tasks: BackgroundTasks,
):

    try:

        print("\n==============================")
        print("Starting note generation")
        print("==============================")

        # =================================================
        # 1. Get YouTube transcript
        # =================================================

        print("Getting transcript...")

        text = get_transcript(
            req.url
        )

        print(
            f"Transcript received: "
            f"{len(text)} characters"
        )

        # =================================================
        # 2. Generate TEXT notes
        # =================================================

        print("Generating text notes...")

        result = (
            build_text_graph()
            .invoke(
                {
                    "transcript": text,
                    "youtube_url": req.url,
                    "language": req.language,
                    "note_type": req.note_type,
                    "diagram_level": req.diagram_level,
                }
            )
        )

        notes = result["final_notes"]

        # =================================================
        # 3. Save text notes immediately
        # =================================================

        note_id = save_notes(
            notes
        )

        print(
            f"Text notes ready: {note_id}"
        )

        # =================================================
        # 4. Start visual analysis in background
        # =================================================

        background_tasks.add_task(
            generate_visuals_background,
            note_id,
            req.url,
        )

        print(
            "Visual analysis scheduled in background."
        )

        # =================================================
        # 5. Return immediately
        # =================================================

        return {
            "note_id": note_id,
            "notes_url": f"/notes/{note_id}",
        }

    except Exception as e:

        print(
            "NOTE GENERATION ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )