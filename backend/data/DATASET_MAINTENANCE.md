# Dataset Maintenance Guide (RGCET Help Desk)

## Goal
This guide explains how to safely maintain chatbot data while keeping answers grounded in approved official sources.

## Data Workspace Purpose
- `raw/`: original input assets (website text dumps, PDFs, manual notes)
- `processed/`: cleaned machine-readable extraction output from raw files
- `structured/`: curated retrieval-facing JSON records (reviewed, support-safe)
- `chunks/`: chunk artifacts generated for retrieval/indexing
- `metadata/`: source tracking and FAQ seed files
- `vector_store/`: persistent ChromaDB files built from chunks

## Where Official Approved Source Links Are Tracked
- `metadata/source_inventory.json`

Each source record tracks fields like:
- `id`
- `path_or_url` (official source link)
- `raw_local_path`
- `category`
- `trust_priority`
- `reviewed`
- notes/status fields

When adding/updating sources, update this file first.

## Where FAQ Seed Records Are Maintained
- `metadata/manual_faq_seed.json`

Use this for high-confidence, reviewed FAQ-style support answers.
Only keep approved, non-placeholder, review-safe content.

## Safe Editing Rules for Structured JSON
Files in `structured/` are retrieval-facing. Follow these rules:
- keep valid JSON arrays of objects
- keep `reviewed: true` only for confirmed official facts
- do not introduce unresolved placeholders in reviewed retrieval records
- include `source_ref` that maps to tracked approved source(s)
- use clear `notes` describing evidence/limitations

Also see:
- `structured/RETRIEVAL_SAFE_EDIT_GUIDE.md`
- `dataset_rules.md`

## How to Update Real Data Later
1. Add or update approved raw source files in `raw/`.
2. Update `metadata/source_inventory.json` with official source URL/path and metadata.
3. Update structured/support records in `structured/` as needed.
4. Keep unsupported or unknown fields out of reviewed retrieval records.

## Placeholders: Replacement and Review
If temporary placeholder records are used during drafting:
- replace placeholders only with verified official values
- set/keep `reviewed: true` only after verification
- keep unresolved placeholders out of retrieval-facing reviewed records
- document remaining uncertainty in `notes`

## Rebuild After Data Changes
Run from `backend/`:
```bash
python scripts/process_raw_data.py
python scripts/chunk_data.py
python scripts/build_vector_store.py
```

Optional sanity check:
```bash
python scripts/verify_vector_store.py
```

## Final Validation Checklist
- source links in `source_inventory.json` are official and current
- structured records are reviewed and placeholder-safe
- chunks were regenerated
- vector store rebuild completed without errors
- key test questions return grounded responses or safe redirects/fallbacks
