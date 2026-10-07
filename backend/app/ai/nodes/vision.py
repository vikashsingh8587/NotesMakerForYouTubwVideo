import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from ...config import GEMINI_API_KEY, GEMINI_VISION_MODEL
from ...services.youtube_service import get_video_duration
from ..state import NoteState

SEGMENT_SECONDS = 20 * 60
FPS = 0.1
MAX_VIDEO_SECONDS = 12 * 60 * 60
VISION_WORKERS = 2
MAX_RETRIES = 4

VISION_PROMPT = """
You are the visual-analysis component of a lecture note generator.

Analyze ONLY the provided lecture video segment.

Extract ONLY visually important educational information:
1. PPT slides
2. Teacher-written board content
3. Diagrams
4. Flowcharts
5. Trees
6. Graphs
7. Tables
8. Formulas
9. Numerical problems
10. Practice questions shown on screen
11. Code shown on screen
12. Important images or illustrations
13. Important handwritten content
14. Comparisons shown visually

Ignore:
- teacher's face
- normal talking-head frames
- decorative animations
- irrelevant backgrounds
- advertisements
- logos unless educationally relevant

For every important visual item provide:
- approximate timestamp
- visual type
- title
- useful educational content
- important visible text

Do not invent text. If a formula, table, diagram, number, label or question cannot be read confidently, do not guess it.
Avoid duplicate entries for the same slide or board state.

Return ONLY valid JSON:
{"visuals":[{"timestamp":"HH:MM:SS","type":"slide","title":"Binary Search Tree","content":"Actual useful educational content visible in the video","important_text":["visible text 1"]}]}

If there are no useful educational visuals: {"visuals":[]}
"""

def seconds_to_timestamp(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

def normalize_timestamp(timestamp: str, segment_start: int) -> str:
    if not timestamp: return seconds_to_timestamp(segment_start)
    timestamp = str(timestamp).strip()
    match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", timestamp)
    if match:
        relative = int(match.group(1))*3600 + int(match.group(2))*60 + int(match.group(3))
        return seconds_to_timestamp(segment_start + relative)
    match = re.match(r"^(\d{1,3}):(\d{2})$", timestamp)
    if match:
        relative = int(match.group(1))*60 + int(match.group(2))
        return seconds_to_timestamp(segment_start + relative)
    return seconds_to_timestamp(segment_start)

def clean_json_output(output_text: str) -> str:
    output_text = (output_text or "").strip()
    if output_text.startswith("```"):
        output_text = re.sub(r"^```(?:json)?\s*", "", output_text, flags=re.IGNORECASE)
        output_text = re.sub(r"\s*```$", "", output_text)
    return output_text.strip()

def _is_temporary_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in ("503", "unavailable", "429", "resource_exhausted", "remoteprotocolerror", "server disconnected", "timed out", "timeout"))

def generate_with_retry(client, contents, max_retries=MAX_RETRIES):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=GEMINI_VISION_MODEL, contents=contents)
        except Exception as exc:
            if not _is_temporary_error(exc):
                print("Gemini visual permanent error:", repr(exc))
                return None
            if attempt == max_retries - 1:
                print("Gemini visual failed after retries:", repr(exc))
                return None
            wait_seconds = 2 * (2 ** attempt)
            print(f"Gemini visual temporary error. Retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)
    return None

def analyze_video_segment(client, youtube_url, start_seconds, end_seconds):
    start_time = seconds_to_timestamp(start_seconds)
    end_time = seconds_to_timestamp(end_seconds)
    print(f"Visual analysis: {start_time} -> {end_time}")
    prompt = f"""
{VISION_PROMPT}

Analyze ONLY this time range:
START: {start_time}
END: {end_time}

Do not analyze outside this range.
Timestamps in the JSON should be relative to this segment.
"""
    contents = types.Content(parts=[
        types.Part(
            file_data=types.FileData(file_uri=youtube_url, mime_type="video/*"),
            video_metadata=types.VideoMetadata(start_offset=f"{start_seconds}s", end_offset=f"{end_seconds}s", fps=FPS),
        ),
        types.Part(text=prompt),
    ])
    response = generate_with_retry(client, contents)
    if response is None: return []
    output_text = clean_json_output(getattr(response, "text", ""))
    if not output_text: return []
    try:
        data = json.loads(output_text)
    except json.JSONDecodeError:
        print("Vision model returned invalid JSON.")
        return []
    visuals = data.get("visuals", [])
    if not isinstance(visuals, list): return []
    normalized = []
    for visual in visuals:
        if not isinstance(visual, dict): continue
        visual["timestamp"] = normalize_timestamp(visual.get("timestamp", ""), start_seconds)
        normalized.append(visual)
    return normalized

def deduplicate_visuals(visuals):
    unique, seen = [], set()
    for visual in visuals:
        title = str(visual.get("title", "")).strip().lower()
        content = str(visual.get("content", "")).strip().lower()
        key = (title, content[:400])
        if key in seen: continue
        seen.add(key)
        unique.append(visual)
    return unique

def _analyze_one_segment(youtube_url, start_seconds, end_seconds):
    client = genai.Client(api_key=GEMINI_API_KEY)
    return analyze_video_segment(client, youtube_url, start_seconds, end_seconds)

def analyze_video_visuals(state: NoteState):
    youtube_url = state.get("youtube_url")
    if not youtube_url or not GEMINI_API_KEY:
        return {"visual_analysis": []}
    if state.get("diagram_level") == "minimal":
        print("Diagram level is minimal. Skipping video visual analysis.")
        return {"visual_analysis": []}

    duration = get_video_duration(youtube_url)
    if duration is None:
        print("Exact video duration unavailable. Skipping visual analysis to avoid unnecessary requests.")
        return {"visual_analysis": []}
    duration = max(1, min(int(duration), MAX_VIDEO_SECONDS))

    ranges = []
    start = 0
    while start < duration:
        end = min(start + SEGMENT_SECONDS, duration)
        ranges.append((start, end))
        start = end

    print(f"Starting visual analysis: duration={seconds_to_timestamp(duration)}, segments={len(ranges)}")
    all_visuals = []
    workers = min(VISION_WORKERS, len(ranges))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_analyze_one_segment, youtube_url, s, e): (s, e) for s, e in ranges}
        for future in as_completed(futures):
            s, e = futures[future]
            try:
                all_visuals.extend(future.result())
            except Exception as exc:
                print(f"Visual segment failed {seconds_to_timestamp(s)} -> {seconds_to_timestamp(e)}: {exc!r}")

    all_visuals = deduplicate_visuals(all_visuals)
    max_visuals = 120 if state.get("diagram_level") == "more" else 60
    all_visuals = all_visuals[:max_visuals]
    print(f"Visual analysis completed. Found {len(all_visuals)} visual items.")
    return {"visual_analysis": all_visuals}
