import sys
import os
import json

# Add the backend root to python path to import modules normally
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_path)

from app.services.retrieve import retrieve_context

queries = [
    "office timings",
    "HOD of CSE",
    "admission office contact",
    "fee payment challan",
    "where is the nearest space station? I want to eat alien food" # Deliberately unrelated or weak query
]

output_file = open("test_out.txt", "w", encoding="utf-8")

for q in queries:
    output_file.write(f"--- QUERY: {q} ---\n")
    result = retrieve_context(q, top_k=2)
    output_file.write(f"No results: {result['no_results']}\n")
    output_file.write(f"Weak results: {result['weak_results']}\n")
    for r in result["results"]:
        output_file.write(f"Distance: {r['distance']:.3f} | Title: {r.get('title', '')} | ID: {r['chunk_id']}\n")
        # output_file.write(f"Text snippet: {r['text'][:50]}...\n")
    output_file.write("\n")

output_file.close()
