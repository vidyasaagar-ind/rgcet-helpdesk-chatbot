import json
import os
import sys

from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.services.retrieve import retrieve_context

QUERIES = [
    "What are the office timings?",
    "Who is the HOD of CSE?",
    "How can I contact the admission office?",
    "Where is the nearest space station?",
]


def main():
    client = TestClient(app)

    for query in QUERIES:
        print("\n" + "=" * 80)
        print(f"Query: {query}")
        retrieval = retrieve_context(query)
        top_distance = retrieval["results"][0]["distance"] if retrieval["results"] else None
        print(
            "retrieval:",
            json.dumps(
                {
                    "no_results": retrieval["no_results"],
                    "weak_results": retrieval["weak_results"],
                    "top_distance": top_distance,
                    "top_chunk_id": retrieval["results"][0]["chunk_id"] if retrieval["results"] else None,
                },
                indent=2,
            ),
        )

        response = client.post("/chat", json={"message": query, "session_id": "debug-script"})
        print(f"chat_status_code: {response.status_code}")
        print("chat_response:", json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
