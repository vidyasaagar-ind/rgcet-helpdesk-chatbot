import os
import chromadb
from chromadb.utils import embedding_functions

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, 'data', 'vector_store')

queries = [
    "office timings",
    "HOD of CSE",
    "admission office contact",
    "fee payment challan"
]

def verify():
    # Load Persistent ChromaDB
    print(f"Connecting to ChromaDB store at: {VECTOR_STORE_DIR}")
    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    collection_name = "rgcet_knowledge"
    
    try:
        # Load embedding function, must be same as used for inserting
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        collection = client.get_collection(name=collection_name, embedding_function=emb_fn)
    except Exception as e:
        print(f"Failed to get collection '{collection_name}': {e}")
        return

    print(f"Collection '{collection_name}' loaded successfully. Total chunks: {collection.count()}")
    
    print("\n" + "="*50)
    print("Running Semantic Verification Lookups")
    print("="*50)
    
    for q in queries:
        print(f"\n[Search Query]: '{q}'\n")
        results = collection.query(
            query_texts=[q],
            n_results=2 # Show top 2 results
        )
        
        if not results['documents'][0]:
            print("  No relevant results found.")
            continue
            
        for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
            # Print excerpt
            excerpt = doc.replace("\n", " ")[:150]
            if len(doc) > 150:
                excerpt += "..."
                
            print(f"  Result {i+1} (Distance: {dist:.4f})")
            print(f"    Excerpt: {excerpt}")
            print(f"    Metadata: {meta.get('category')} | {meta.get('source_type')} | ID: {meta.get('source_record_id')}")

if __name__ == "__main__":
    verify()
