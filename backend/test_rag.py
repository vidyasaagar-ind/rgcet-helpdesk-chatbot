import json
from app.services.retrieve import retrieve_context

query = "What are the office timings?"
result = retrieve_context(query)
print("RETRIEVAL DONE")
with open("rag_out_clean.json", "w") as f:
    json.dump(result, f, indent=2)
