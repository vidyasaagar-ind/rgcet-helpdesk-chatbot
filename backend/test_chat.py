import asyncio
from app.models.schemas import ChatRequest
from app.routes.chat import chat_interaction

async def test():
    queries = [
        "How can I contact the admission office?",
        "Where can I get the fee payment challan?",
        "Tell me about the placement cell.",
        "Who is the HOD of CSE?",
        "What are the office timings?",
        "Where is the nearest space station?"
    ]
    for q in queries:
        req = ChatRequest(message=q, session_id="test")
        res = await chat_interaction(req)
        print(f"\nQuery: {q}")
        print(f"Answer: {res.answer}")
        print(f"Mode: {res.response_mode}, Status: {res.status}")

asyncio.run(test())
