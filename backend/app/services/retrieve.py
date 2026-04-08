from typing import Any, Dict, Optional

import chromadb
from chromadb.utils import embedding_functions

from app.core.config import settings
from app.services.logging_service import app_logger

COLLECTION_NAME = "rgcet_knowledge"


class RetrieverService:
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_fn = None
        self.vector_store_dir = settings.resolved_chroma_db_path
        self._initialize()

    def _initialize(self):
        try:
            self.client = chromadb.PersistentClient(path=self.vector_store_dir)
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            self.collection = self.client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=self.embedding_fn,
            )
            app_logger.info(
                "Retriever initialized with collection '%s' at '%s'.",
                COLLECTION_NAME,
                self.vector_store_dir,
            )
        except Exception as exc:
            app_logger.warning(
                "Retriever initialization failed for '%s': %s",
                self.vector_store_dir,
                exc,
            )
            self.collection = None

    def retrieve_chunks(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve chunks and expose conservative signals for routing and debugging.
        """
        if not self.collection:
            return {
                "results": [],
                "no_results": True,
                "weak_results": False,
                "message": "Vector store not initialized or not found.",
            }

        chroma_where = filters or None
        requested_top_k = top_k or settings.top_k_results

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=requested_top_k,
                where=chroma_where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            app_logger.exception("Retriever query failed for '%s': %s", query, exc)
            return {
                "results": [],
                "no_results": True,
                "weak_results": False,
                "message": f"Query error: {exc}",
            }

        if not results.get("documents") or not results["documents"][0]:
            app_logger.info("Retriever found no results for '%s'.", query)
            return {
                "results": [],
                "no_results": True,
                "weak_results": False,
            }

        structured_results = []
        is_weak = True
        threshold = settings.similarity_threshold

        for doc_id, doc, meta, distance in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            if distance <= threshold:
                is_weak = False

            metadata = meta or {}
            structured_results.append(
                {
                    "chunk_id": doc_id,
                    "text": doc,
                    "title": metadata.get("title", ""),
                    "category": metadata.get("category", ""),
                    "department": metadata.get("department", ""),
                    "source_type": metadata.get("source_type", ""),
                    "source_ref": metadata.get("source_ref", ""),
                    "trust_priority": metadata.get("trust_priority", ""),
                    "reviewed": metadata.get("reviewed", False),
                    "notes": metadata.get("notes", ""),
                    "distance": distance,
                }
            )

        top_distance = structured_results[0]["distance"] if structured_results else None
        app_logger.info(
            "Retrieval diagnostics | query='%s' | results=%s | no_results=%s | weak_results=%s | top_distance=%s | threshold=%s",
            query,
            len(structured_results),
            len(structured_results) == 0,
            is_weak,
            f"{top_distance:.4f}" if top_distance is not None else "n/a",
            threshold,
        )

        return {
            "results": structured_results,
            "no_results": len(structured_results) == 0,
            "weak_results": is_weak,
        }


retriever = RetrieverService()


def retrieve_context(
    query: str,
    top_k: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return retriever.retrieve_chunks(query, top_k, filters)
