# Retrieval-Safe Dataset Guide

These refined files are designed to improve RAG retrieval quality.

## Key rule
Do not keep editable placeholders inside retrieval-indexed structured records when the chatbot is already live.
Placeholders like `[HOD_CSE_NAME]` and `[OFFICE_OPEN_TIME]` are likely to leak into answers.

## What changed
- Placeholder-only records were removed from retrieval-facing files.
- Support-style official records were added for:
  - HOD queries
  - office timing queries
  - admission support
  - transport support
  - principal support
  - department count support
- Department records were reduced to verified facts only.

## How to add missing real data later
When you get confirmed official data:
1. Add a reviewed=true official record with a real source_ref.
2. Rebuild:
   - process_raw_data.py
   - chunk_data.py
   - build_vector_store.py
3. Test the affected query again.

## Where to keep editable placeholders
Keep future placeholders in a non-indexed template file or documentation file until the values are confirmed.
