How to explain this project during demo (very important)

Use this structure:

Problem

College websites usually:

scatter information across pages
lack structured help systems
require manual navigation
provide no conversational interface
Solution

A domain-restricted AI help desk chatbot that:

answers only approved college information
avoids hallucination
redirects when data unavailable
supports future dataset updates safely
Architecture

Explain simply:

User → Widget → FastAPI → Vector Search → Approved Dataset → Answer

Optional:

Gemini (optional enhancement layer)
Key technical feature (your strongest point)

Say this clearly:

The chatbot does not generate answers from the internet.
It retrieves verified college information from a structured knowledge base using a Retrieval-Augmented Generation pipeline.

This is exactly what faculty want to hear.

Expected viva questions (prepare answers)
Q: Why not train a custom ML chatbot?

Correct answer:

Because institutional chatbots must avoid hallucination. RAG ensures answers come only from approved sources and remain maintainable without retraining models.

Q: Why retrieval-only mode exists?

Correct answer:

To guarantee deterministic responses when LLM quota or connectivity is unavailable.

Q: How can data be updated later?

Correct answer:

Update structured dataset → rerun chunk pipeline → rebuild vector store.

No retraining required.

Q: Can this integrate with college website?

Correct answer:

Yes. The widget is portable JavaScript and only requires changing API_BASE_URL.

Q: Why some answers redirect instead of answering?

Correct answer:

Because the system intentionally avoids guessing when official sources do not publish verified data.

This is a safety design decision.

What your project now qualifies as

Technically, this is:

Domain-restricted Retrieval-Augmented Institutional Support Chatbot Prototype

That is a strong mini-project classification.