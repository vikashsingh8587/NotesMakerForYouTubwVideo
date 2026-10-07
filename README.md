# Lecture Notes AI

Fast Chrome extension + FastAPI + LangGraph + Gemini pipeline for YouTube lecture notes.

## Processing flow

- Transcript is cached locally.
- Text chunks are analyzed with up to 2 concurrent Gemini requests.
- Text notes are saved first and returned immediately after text generation.
- Visual analysis runs in the FastAPI background task.
- Exact YouTube duration is read with yt-dlp, so a 10-minute video is analyzed as one 10-minute segment instead of looping to 12 hours.
- Visual analysis uses 20-minute maximum segments and at most 2 concurrent visual requests.
- Temporary Gemini/network failures are retried.
- A visual failure never deletes the generated text notes.
- The notes page polls the visual status and refreshes automatically when visuals finish.

## Setup

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and put your Gemini API key in it.

Run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Then load the `extension` folder as an unpacked Chrome extension.

## Security

Never commit or share `backend/.env`. If an API key has been exposed, revoke/rotate it before continuing.
