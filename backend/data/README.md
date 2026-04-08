# Backend Data Workspace

This directory contains source data, processed artifacts, and retrieval/index assets for the RGCET chatbot.

## Folder Map
- `raw/`: approved source files grouped by type (`website`, `pdf`, `txt`, `notes`, `manual`)
- `processed/`: cleaned extraction outputs generated from raw sources
- `structured/`: curated structured JSON records used by retrieval
- `chunks/`: generated chunk files for retrieval indexing
- `metadata/`: source inventory and FAQ seed files
- `vector_store/`: ChromaDB persistent store

## Primary Maintenance Docs
- `DATASET_MAINTENANCE.md` (full update workflow)
- `dataset_rules.md` (source/trust policy)
- `structured/RETRIEVAL_SAFE_EDIT_GUIDE.md` (retrieval-safe editing rules)
