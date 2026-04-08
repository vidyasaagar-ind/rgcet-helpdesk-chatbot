# Gemini Generator Service Documentation

## Overview
This document outlines the architecture and design of the generative answer layer for the RGCET Help Desk chatbot, implemented in `backend/app/services/generator.py`. This layer utilizes the Gemini LLM (specifically `gemini-1.5-flash`) to generate human-readable, grounded answers based solely on information retrieved from the knowledge base vector store.

## Gemini Integration Architecture
The generator service connects the retrieval pipeline (ChromaDB) to the generative pipeline (Gemini). The `/chat` endpoint handles user requests by first passing the query to the retrieval block `retrieve_context(query)`, and then passing both the query and the retrieved chunks to the `generate_answer(query, chunks, weak_results)` function.
If a placeholder API key is detected, the generator safely mocks the LLM interaction to prevent crashes while ensuring the exact expected response schema.

## Grounding Prompt Logic
The core of the LLM interaction is the structured grounding prompt. Chunks are linearly concatenated within the prompt sequence to act as context. 
The instructions explicitly compel the LLM to act as the "RGCET AI Help Desk assistant," and constrain its ability to answer external questions. 
```text
Answer ONLY using the information provided below.
If the answer is not contained in the context, reply:
'I could not find reliable information in the approved college knowledge base.'

Do NOT guess.
Do NOT use external knowledge.
Do NOT fabricate names, timings, or contacts.
```

## Fallback Behavior
The service handles out-of-domain knowledge queries dynamically.
1. **At the retrieval level**: If ChromaDB cannot find relevant documents (or distances exceed the threshold yielding `weak_results=True`) or returns 0 chunks, Gemini generation is entirely bypassed to save latency and cost.
2. **At the generation level**: If the LLM generates the targeted unanswerable phrase "I could not find reliable information...", the system parses this and flips the `grounded` flag to `False` in its structured output.

## Safety Constraints
Safety is enforced through multiple layers:
1. Input queries are checked against malicious patterns (via `guardrails.py`) before processing.
2. The model is strictly instructed not to guess or fabricate information.
3. The model is given a strict fallback response if information is missing in context.
4. Outputs are structured consistently regardless of internal failure states.

## Environment Variables Required
The service relies on the following environment variables (defined in `.env`):
- `GEMINI_API_KEY`: Authentication for Google's Gemini SDK.
- `MODEL_NAME`: The model version. Defaults to `gemini-1.5-flash`.
- `TOP_K_RESULTS`: The number of chunks passed as context.
- `SIMILARITY_THRESHOLD`: The semantic boundary determining if retrieved results are "weak".

## Intentionally Not Implemented Yet
- **Frontend Integration**: The client-side UI is not yet connected to the augmented `/chat` endpoint.
- **Streaming Tokens**: Responses are generated as full text blocks (latency exists). Streaming text generation for a typing effect is intentionally omitted until the core JSON structure is reliable.
- **Conversational Memory**: The LLM prompt focuses solely on single turn QA. Conversation history or memory context is not injected yet.
