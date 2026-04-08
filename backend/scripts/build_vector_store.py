import os
import json
import chromadb
from chromadb.utils import embedding_functions

# Model choice: We will use all-MiniLM-L6-v2 which is Chroma's default sentence-transformer.
# It is a highly practical, lightweight local model suitable for semantic text similarity.
# It requires no paid API keys and processes chunks entirely locally.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CHUNKS_FILE = os.path.join(DATA_DIR, 'chunks', 'all_chunks.json')
VECTOR_STORE_DIR = os.path.join(DATA_DIR, 'vector_store')

def build_store():
    if not os.path.exists(CHUNKS_FILE):
        print(f"[Error] Chunks file not found at {CHUNKS_FILE}")
        return

    with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks.")

    # Setup Persistent ChromaDB
    # To assure a clean, repeatable rebuild, we will delete the collection if it exists.
    # This prevents duplicates and ensures the latest schema and vectors are indexed.
    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    
    collection_name = "rgcet_knowledge"
    
    try:
        # Recreate collection cleanly
        client.delete_collection(name=collection_name)
        print(f"Deleted existing collection '{collection_name}' for clean rebuild.")
    except ValueError:
        # Collection does not exist
        pass
    except Exception as e:
        print(f"Delete collection details (safe to ignore if not exists): {e}")
    
    # Initialize embedding model
    print(f"Initializing embedding model 'all-MiniLM-L6-v2'...")
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    collection = client.create_collection(
        name=collection_name, 
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"} # Cosine similarity represents text matching well
    )
    
    documents = []
    ids = []
    metadatas = []
    
    for c in chunks:
        # Use chunk_id as stable document ID
        ids.append(c["chunk_id"])
        
        # Use text field as the embedding input
        documents.append(c["text"])
        
        # Preserve and flatten metadata safely for ChromaDB
        meta = {}
        for k, v in c.items():
            if k not in ["chunk_id", "text"]:
                if v is None:
                    continue # Chroma metadata cannot hold null values
                elif isinstance(v, (str, int, float, bool)):
                    meta[k] = v
                else:
                    meta[k] = str(v) # Flatten complex types
        metadatas.append(meta)
    
    print(f"Embedding {len(documents)} chunks... This might take a moment.")
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    print(f"Successfully inserted {collection.count()} chunks into '{collection_name}' collection.")
    print(f"Store saved locally at: {VECTOR_STORE_DIR}")

if __name__ == "__main__":
    build_store()
