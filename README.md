# RGCET Help Desk Chatbot (Prototype v3)

## Purpose
This project is an RGCET-focused Help Desk chatbot prototype that answers student-facing questions using approved college sources only.

It is designed for:
- local demo and review
- faculty/technical handoff
- controlled future dataset updates

## Architecture Overview
The system has three main layers:

1. Widget frontend (`chatbot-widget/`)
- A portable HTML/CSS/JS chatbot widget.
- Sends user queries to backend `POST /chat`.

2. FastAPI backend (`backend/`)
- Accepts chat messages and validates input.
- Retrieves relevant chunks from ChromaDB.
- Responds in one of three modes:
  - `gemini` (when enabled and available)
  - `retrieval_only` (safe non-LLM answer from approved records)
  - `retrieval_redirect`/`fallback` (official contact/link guidance when exact fact is missing)

3. Data and retrieval pipeline (`backend/data/` + `backend/scripts/`)
- Raw approved files -> processed JSON -> chunks -> Chroma vectors.
- Retrieval is grounded in indexed approved data.

## Major Folders
- `backend/app/`: FastAPI app, routes, retrieval/generation services
- `backend/scripts/`: data processing, chunking, vector build scripts
- `backend/data/raw/`: source files (website text, pdfs, manual notes)
- `backend/data/processed/`: cleaned extracted records from raw sources
- `backend/data/structured/`: curated structured records used for retrieval
- `backend/data/chunks/`: chunk artifacts used for vectorization
- `backend/data/metadata/`: source inventory + FAQ seed tracking
- `backend/data/vector_store/`: persistent ChromaDB files
- `chatbot-widget/`: deployable frontend widget and local demo shell

## High-Level Chat Flow
1. User sends message from widget.
2. Backend `/chat` retrieves top chunks from ChromaDB.
3. If retrieval is strong:
- Gemini path is used only when `USE_GEMINI=true` and a valid key is available.
- Otherwise retrieval-only answering is used.
4. If exact fact is missing but safe official contact/link exists, backend returns a redirect-style grounded response.
5. If no safe grounded support exists, backend returns fallback text.

## Supported Query Categories
- admissions eligibility/contact/inquiry support
- official contact information
- fee challan and forms guidance
- placement guidance
- department/program coverage summaries
- college overview and location
- bus/transport official-link guidance
- leadership support (principal/HOD support with safe limits)

## Known Limitations
- Some department pages are gallery pages and do not publish full profiles.
- Confirmed HOD names may still be unavailable unless later approved sources are added.
- Office timings are not officially published in current approved sources.
- Exact admission office room location is not separately published.
- Bus route image/PDF still requires manual review for exact stops/fees.
- Gemini may hit quota/traffic limits; retrieval-only mode is the rescue path.

See also: `LIMITATIONS_AND_USAGE_BOUNDARIES.md`.

## Local Run (Quick Start)
1. Start backend:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

2. Start widget demo shell (new terminal):
```bash
cd chatbot-widget
python -m http.server 5500
```
Open: `http://127.0.0.1:5500`

3. Optional retrieval-only test mode:
- Set `USE_GEMINI=false` in `backend/.env`.

## Rebuild Data Pipeline (after data edits)
```bash
cd backend
python scripts/process_raw_data.py
python scripts/chunk_data.py
python scripts/build_vector_store.py
```

## Handoff Docs
- Backend setup: `backend/README.md`
- Widget integration: `chatbot-widget/README.md`
- Dataset maintenance: `backend/data/DATASET_MAINTENANCE.md`
- Website/faculty handoff: `HANDOFF_GUIDE.md`
- Usage boundaries and limitations: `LIMITATIONS_AND_USAGE_BOUNDARIES.md`
