# RGCET Help Desk Backend

## Overview
This backend is a FastAPI service that powers the RGCET chatbot.

Core responsibilities:
- receive chat queries at `POST /chat`
- retrieve grounded context from ChromaDB
- generate response using Gemini (optional) or retrieval-only fallback paths
- enforce safe fallback/redirect behavior when exact facts are unavailable

## Tech and Runtime
- Python: tested on `Python 3.14.3`
- Framework: FastAPI + Uvicorn
- Vector DB: ChromaDB (`backend/data/vector_store`)

## Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Configuration
Copy example file:
```bash
copy .env.example .env
```

### Where to place Gemini API key
Edit `backend/.env`:
- `GEMINI_API_KEY=<your_actual_key>`

### What `USE_GEMINI` does
- `USE_GEMINI=true`:
  - Backend attempts Gemini generation when retrieval is strong and key/model are available.
- `USE_GEMINI=false`:
  - Backend skips Gemini and uses retrieval-only + safe redirect/fallback behavior.

Recommended for functional QA and deterministic demo verification:
- `USE_GEMINI=false`

## Run Backend
From `backend/`:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Useful endpoints:
- `GET /health`
- `POST /chat`
- Swagger: `http://127.0.0.1:8000/docs`

## Data Rebuild Pipeline
Run these in order after source/dataset edits:

```bash
cd backend
python scripts/process_raw_data.py
python scripts/chunk_data.py
python scripts/build_vector_store.py
```

What each script does:
- `process_raw_data.py`: reads approved inventory items and creates cleaned files in `data/processed/`
- `chunk_data.py`: builds retrieval-safe chunks into `data/chunks/`
- `build_vector_store.py`: rebuilds Chroma collection `rgcet_knowledge` from `all_chunks.json`

## Retrieval-Only Testing Guidance
Use retrieval-only mode when you want stable behavior independent of Gemini quota/traffic.

1. Set in `.env`:
```env
USE_GEMINI=false
```
2. Start backend and test `/chat` from widget or API client.
3. Confirm responses are grounded and use redirect/fallback only when exact facts are unavailable.

## Known Data Limitations
- Some department sources are gallery-only pages without full profile fields.
- HOD names are intentionally absent when not confirmed in approved sources.
- Office timings are not published in currently approved sources.
- Admission office exact room location is not separately published.
- Bus route chart/fee specifics still require manual review of official image/PDF.

## Related Docs
- Root project: `../README.md`
- Dataset maintenance: `data/DATASET_MAINTENANCE.md`
- Limitations note: `../LIMITATIONS_AND_USAGE_BOUNDARIES.md`
