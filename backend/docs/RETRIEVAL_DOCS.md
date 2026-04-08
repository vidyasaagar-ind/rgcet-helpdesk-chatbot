# RGCET Help Desk Retrieval Layer

## Overview
This document covers the implementation details of the semantic retrieval service for the RGCET local ChromaDB vector store. 

**Module Path**: `backend/app/services/retrieve.py`

## How Retrieval Works
1. **Connection**: The module instantiates a `chromadb.PersistentClient` pointing to `backend/data/vector_store/` and connects to the existing `rgcet_knowledge` collection.
2. **Embedding**: Before querying, user queries are automatically embedded inline using the lightweight local model `all-MiniLM-L6-v2` (`SentenceTransformerEmbeddingFunction`).
3. **Semantic Search**: We compare the embedded query vector with our chunks using Cosine Distance (0 = perfect semantic match, 2 = total opposite). 
4. **Structured Mapping**: Chroma returns a list of dictionaries with chunks, ids, metadata, and distance metrics. The retrieval module unwraps these lists and reshapes them into clean, structured Python dictionaries mapping all stored knowledge correctly.

## `top_k` Strategy
The system uses a default `top_k = 4`, meaning it retrieves the four semantic best chunks from the knowledge base for a query. This can be easily tuned via the `top_k` keyword parameter in the `retrieve_chunks()` or `retrieve_context()` function for more extensive or concise context gathering.

## Metadata and Source
Rich metadata enables post-fetching filtering or structured generation. Key metadata keys extracted from the Chroma store include:
- `title`, `category`, `department`, `source_type`, `source_ref`, `trust_priority`, `reviewed`, `notes`.
They are safely extracted during querying using `.get("key", default)` and piped exactly into the response objects so generation logic will have complete grounding information. 

## Handling Weak & Irrelevant Results
To handle out-of-domain interactions safely without inventing details or polluting context, the system calculates distance thresholds:
- **`WEAK_DISTANCE_THRESHOLD = 0.65`**: Any returned document query that yields a distance > 0.65 is typically unrelated out-of-distribution noise when using `all-MiniLM-L6-v2`. 
- **Flags**: If *all* returned document distances exceed `0.65`, `weak_results: True` is flagged in the response format.
- If the knowledge collection itself returns 0 hits, `no_results: True` is triggered.
This avoids "I don't know" logic in the retrieval engine but delegates it gracefully to the downstream generation nodes.

## What is Intentionally NOT Implemented Yet
- **Final Answer Generation**: No calls to LLMs (like Gemini) exist here. 
- **User-Facing Responses**: The retrieval layer purely returns JSON shapes and internal metadata, not chat sentences to output.
- **Reranking**: Advanced cross-encoder reranking layers are excluded for speed and simplicity in this pipeline iteration.
- **Frontend Integration**: No API endpoints or web interfaces communicate with this logic.

## Filtering
Metadata-based filtering is designed using a clean passthrough of a dictionary representation of Chroma's `where` clauses (`where={"category": "admissions"}`). This readies the service for future explicit metadata parameters if desired.
