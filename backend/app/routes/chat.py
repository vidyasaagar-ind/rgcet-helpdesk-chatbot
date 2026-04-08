from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.models.schemas import ChatRequest, ChatResponse
from app.services.guardrails import check_input_cleanliness
from app.services.retrieve import retrieve_context
from app.services.generator import generate_answer
from app.services.logging_service import app_logger

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_interaction(request: ChatRequest):
    """
    Handles user chat interactions.
    Integrates the semantic retrieval and grounded text generator layers.
    """
    query = request.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # 1. Input Guardrails
    if not check_input_cleanliness(query):
        raise HTTPException(status_code=400, detail="Invalid input detected.")

    app_logger.info(f"Processing query: '{query}' for session: {request.session_id}")

    retrieval_response = retrieve_context(query, top_k=settings.top_k_results)
    top_distance = None
    if retrieval_response.get("results"):
        top_distance = retrieval_response["results"][0].get("distance")

    app_logger.info(
        "Chat route retrieval summary | query='%s' | chunks=%d | top_titles=%s | top_distance=%s | no_results=%s | weak_results=%s",
        query,
        len(retrieval_response.get("results", [])),
        [c.get("title") for c in retrieval_response.get("results", [])[:2]],
        f"{top_distance:.4f}" if top_distance is not None else "n/a",
        retrieval_response.get("no_results", True),
        retrieval_response.get("weak_results", False),
    )

    generation_result = generate_answer(
        query=query, 
        chunks=retrieval_response.get("results", []), 
        weak_results=retrieval_response.get("weak_results", False)
    )

    app_logger.info(
        "Chat route generation summary | query='%s' | response_mode=%s | fallback_type=%s | grounded=%s | sources_used=%s",
        query,
        generation_result.get("response_mode", "fallback"),
        generation_result.get("fallback_type", "generic"),
        generation_result.get("grounded", False),
        generation_result.get("sources_used", 0),
    )

    return ChatResponse(
        answer=generation_result["answer"],
        status="grounded" if generation_result["grounded"] else "fallback",
        source_count=generation_result["sources_used"],
        grounded=generation_result["grounded"],
        sources_used=generation_result["sources_used"],
        weak_results=generation_result["weak_results"],
        response_mode=generation_result["response_mode"],
        fallback_type=generation_result.get("fallback_type", "generic"),
        no_results=retrieval_response.get("no_results", True),
    )
