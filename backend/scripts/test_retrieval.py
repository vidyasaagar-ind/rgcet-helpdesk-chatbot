import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.retrieve import retrieve_context

def test_queries():
    queries = [
        "office timings",
        "HOD of CSE",
        "admission office contact",
        "fee payment challan",
        "what is the recipe for chocolate cake" # Deliberately unrelated/weak query
    ]

    for q in queries:
        print(f"\n{'='*50}\nQuery: '{q}'\n{'='*50}")
        response = retrieve_context(query=q, top_k=2)
        
        print(f"No Results Flag: {response['no_results']}")
        print(f"Weak Results Flag: {response['weak_results']}")
        
        for i, res in enumerate(response['results']):
            print(f"\n[Result {i+1}] Distance: {res['distance']:.4f} | Chunk ID: {res['chunk_id']}")
            print(f"Title: {res['title']}")
            print(f"Category: {res['category']} | Department: {res['department']} | Priority: {res['trust_priority']}")
            
            # Print a snippet of the text
            text_snippet = res['text'].replace('\n', ' ')[:100] + "..." if len(res['text']) > 100 else res['text'].replace('\n', ' ')
            print(f"Text Snippet: {text_snippet}")

if __name__ == "__main__":
    test_queries()
