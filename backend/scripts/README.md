# Backend Scripts

Run all commands from `backend/` with the project virtual environment activated.

## Pipeline Scripts
- `python scripts/process_raw_data.py`
  - Reads `data/metadata/source_inventory.json`
  - Extracts/cleans supported raw files into `data/processed/`

- `python scripts/chunk_data.py`
  - Builds retrieval chunks from `data/structured/` and `data/processed/`
  - Writes `structured_chunks.json`, `processed_chunks.json`, `all_chunks.json`

- `python scripts/build_vector_store.py`
  - Rebuilds Chroma collection `rgcet_knowledge` from `data/chunks/all_chunks.json`

## Optional Verification Scripts
- `python scripts/verify_vector_store.py`
  - Runs quick semantic checks against the local vector store

- `python scripts/test_retrieval.py`
  - Prints retrieval diagnostics for sample queries

## Typical Rebuild Sequence
```bash
python scripts/process_raw_data.py
python scripts/chunk_data.py
python scripts/build_vector_store.py
```
