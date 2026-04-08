from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's query text.")
    session_id: Optional[str] = Field(None, description="Optional anonymous session ID for tracking.")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="The generated response from the chatbot.")
    status: str = Field(..., description="Status of the interaction, e.g., 'success', 'placeholder', 'error'.")
    source_count: int = Field(default=0, description="Number of knowledge base sources retrieved.")
    grounded: bool = Field(default=False, description="True when the answer is grounded in retrieved knowledge-base content.")
    sources_used: int = Field(default=0, description="Number of sources actually used to form the answer.")
    weak_results: bool = Field(default=False, description="True when retrieved matches are too weak to trust.")
    response_mode: str = Field(default="fallback", description="Answer path used: gemini, retrieval_only, or fallback.")
    fallback_type: str = Field(default="generic", description="supported, redirect, or generic.")
    no_results: bool = Field(default=False, description="True when retrieval returned no chunks.")

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
