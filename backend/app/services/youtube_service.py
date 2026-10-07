import re
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import IpBlocked, NoTranscriptFound, TranscriptsDisabled

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "transcript_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def extract_video_id(url: str) -> str:
    patterns = [r"(?:v=)([A-Za-z0-9_-]{11})", r"(?:youtu\.be/)([A-Za-z0-9_-]{11})", r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})", r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL")

def get_cache_path(video_id: str) -> Path:
    return CACHE_DIR / f"{video_id}.txt"

def get_duration_cache_path(video_id: str) -> Path:
    return CACHE_DIR / f"{video_id}.duration"

def load_cached_transcript(video_id: str):
    path = get_cache_path(video_id)
    if not path.exists(): return None
    try: return path.read_text(encoding="utf-8")
    except OSError: return None

def save_cached_transcript(video_id: str, transcript: str):
    try: get_cache_path(video_id).write_text(transcript, encoding="utf-8")
    except OSError: pass

def load_cached_duration(video_id: str):
    path = get_duration_cache_path(video_id)
    if not path.exists(): return None
    try:
        value = int(path.read_text(encoding="utf-8").strip())
        return value if value > 0 else None
    except (OSError, ValueError): return None

def save_cached_duration(video_id: str, duration: int):
    try: get_duration_cache_path(video_id).write_text(str(int(duration)), encoding="utf-8")
    except OSError: pass

def transcript_duration(fetched) -> int:
    latest = 0.0
    for item in fetched:
        latest = max(latest, float(item.start) + float(item.duration))
    return int(latest)

def get_video_duration(url: str):
    video_id = extract_video_id(url)
    cached = load_cached_duration(video_id)
    if cached: return cached
    try:
        from yt_dlp import YoutubeDL
        options = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
        duration = info.get("duration")
        if duration:
            duration = int(duration)
            save_cached_duration(video_id, duration)
            return duration
    except Exception as exc:
        print("Could not read exact YouTube duration:", repr(exc))
    return None

def transcript_to_text(fetched) -> str:
    return "\n".join(item.text for item in fetched)

def get_transcript(url: str) -> str:
    video_id = extract_video_id(url)
    cached = load_cached_transcript(video_id)
    if cached:
        print(f"Using cached transcript for video: {video_id}")
        return cached
    api = YouTubeTranscriptApi()
    try:
        transcript_list = api.list(video_id)
    except IpBlocked as exc:
        raise RuntimeError("YouTube is temporarily blocking transcript requests from this IP. Please wait before trying another video.") from exc
    except TranscriptsDisabled as exc:
        raise RuntimeError(f"Transcripts are disabled for video: {video_id}") from exc
    except NoTranscriptFound as exc:
        raise RuntimeError(f"No transcript was found for video: {video_id}") from exc

    selected = None
    for transcript in transcript_list:
        if transcript.language_code == "en" and not transcript.is_generated:
            selected = transcript; break
    if selected is None:
        for transcript in transcript_list:
            if transcript.language_code == "en": selected = transcript; break
    if selected is None:
        for transcript in transcript_list:
            if transcript.language_code == "hi" and not transcript.is_generated:
                selected = transcript; break
    if selected is None:
        for transcript in transcript_list:
            if transcript.language_code == "hi": selected = transcript; break
    if selected is None:
        for transcript in transcript_list:
            selected = transcript; break
    if selected is None:
        raise RuntimeError(f"No transcript available for video: {video_id}")

    try:
        fetched = selected.fetch()
        text = transcript_to_text(fetched)
        duration = transcript_duration(fetched)
        if duration > 0:
            save_cached_duration(video_id, duration)
    except IpBlocked as exc:
        raise RuntimeError(f"YouTube blocked the transcript request for video {video_id}.") from exc
    if not text.strip():
        raise RuntimeError(f"Transcript is empty for video: {video_id}")
    save_cached_transcript(video_id, text)
    print(f"Transcript cached for video: {video_id}")
    return text
