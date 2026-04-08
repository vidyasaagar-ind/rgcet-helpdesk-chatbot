import sys
import os
import json

base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_path)

from app.services.retrieve import retrieve_context
from app.services.generator import generate_answer

queries = [
    "office timings",
    "HOD of CSE",
    "admission office contact",
    "fee payment challan",
    "where is the nearest space station? I want to eat alien food" # Deliberately unrelated or weak query
]

output_file = open("test_generator_out.txt", "w", encoding="utf-8")

for q in queries:
    output_file.write(f"--- QUERY: {q} ---\n")
    if q == "where is the nearest space station? I want to eat alien food":
        mock_chunks = []
        weak_results = True
    else:
        mock_chunks = [{"title": "Doc 1", "text": f"Information about {q}."}]
        weak_results = False

    gen_res = generate_answer(
        q, 
        chunks=mock_chunks, 
        weak_results=weak_results
    )
    output_file.write(f"Answer: {gen_res['answer']}\n")
    output_file.write(f"Grounded: {gen_res['grounded']}\n")
    output_file.write(f"Weak Results: {gen_res['weak_results']}\n")
    output_file.write(f"Sources Used: {gen_res['sources_used']}\n")
    output_file.write("\n")

output_file.close()
