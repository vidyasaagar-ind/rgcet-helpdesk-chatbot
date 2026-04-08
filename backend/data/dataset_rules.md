# RGCET Dataset Rules and Guidelines

This document outlines the strict guidelines governing data ingestion for the RGCET Help Desk chatbot RAG pipeline.

## 1. Allowed Sources
*   All data entering the workspace MUST originated from **officially approved RGCET sources**.
*   **No automated blind web scraping** of external unverified academic sites or informal forums.
*   Source URLs and document paths must be explicitly tracked inside `metadata/source_inventory.json`.

## 2. Trust Model & Hierarchies
Data retrieval conflicts are resolved using the **Trust Priority** model.
*   **Priority 1: Manually curated FAQs** (`manual_faq_seed.json`). These are reviewed and locked truths.
*   **Priority 2: Cleaned official website content** (e.g., text directly ported from `www.rgcetpdy.ac.in`).
*   **Priority 3: Approved PDF documents** (circulars, syllabi, official forms handled natively).
*   **Priority 4: Raw notes/manual textual entries** (temporary sources heavily subject to verification and review).

## 3. Data Flow
1.  **Raw Files:** All unprocessed files must land in the corresponding `raw/{type}/` subfolder.
2.  **Cleaning:** No raw string or PDF is to be embedded directly. It must be processed, normalized, and stripped of garbage before moving to `processed/`.
3.  **Chunking:** Only processed content transitions into `chunks/` where semantic sizing occurs.
4.  **Vectorization:** Final chunks are embedded and registered into `vector_store/`.

## 4. Source Metatagging
When content moves from `raw` down the pipeline, the original source payload (e.g., `id`, `path_or_url`) must travel with every chunk. This ensures grounded citations dynamically point users back to the specific PDF or department webpage the bot learned from. Outdated or conflicting sources must be regularly tagged as `status = outdated` in the inventory.
