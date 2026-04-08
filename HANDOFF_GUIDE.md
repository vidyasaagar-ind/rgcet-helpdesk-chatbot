# Handoff Guide (Website Team / HOD)

## What Belongs to the Widget
Required widget assets:
- `chatbot-widget/widget.js`
- `chatbot-widget/widget.css`

Optional local demo shell (not required for production embedding):
- `chatbot-widget/index.html`

## What the Backend Requires
Backend service folder:
- `backend/`

Minimum runtime requirements:
- Python virtual environment
- dependencies from `backend/requirements.txt`
- populated `backend/.env` (from `.env.example`)
- built vector store in `backend/data/vector_store/`

## How API Base URL Works
Widget requests are sent to:
- `POST <API_BASE_URL>/chat`

Set in:
- `chatbot-widget/widget.js` -> `const API_BASE_URL = "..."`

Example production value:
- `https://chatbot-api.yourcollegedomain.edu`

## What Must Be Hosted Where
1. Backend host (API server)
- host FastAPI app from `backend/`
- expose `/chat` and `/health`

2. Frontend host (college website)
- host `widget.js` and `widget.css` as static assets
- embed widget HTML block into target page/template
- point `API_BASE_URL` to backend host

## Demo Page vs Portable Widget
- `index.html` is only a local demo shell.
- The portable widget is the markup + `widget.css` + `widget.js`.
- Production integration should use existing college page templates, not the demo shell page.

## Data Governance Reminder
- Keep dataset updates strictly from approved official sources.
- Update `backend/data/metadata/source_inventory.json` when sources change.
- Rebuild pipeline after data edits:
  - `process_raw_data.py`
  - `chunk_data.py`
  - `build_vector_store.py`
- Preserve transparent limitations rather than guessing unsupported facts.
