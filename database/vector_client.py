import os
import requests
import json
import math
from dotenv import load_dotenv

load_dotenv(override=True)

MISTRAL_LOCAL_URL = os.getenv("MISTRAL_LOCAL_URL")
if MISTRAL_LOCAL_URL:
    MISTRAL_LOCAL_URL = MISTRAL_LOCAL_URL.rstrip('/')
MISTRAL_LOCAL_MODEL = os.getenv("MISTRAL_LOCAL_MODEL")

if not MISTRAL_LOCAL_URL or not MISTRAL_LOCAL_MODEL:
    raise ValueError("MISTRAL_LOCAL_URL or MISTRAL_LOCAL_MODEL is not set in the .env file")

# Cache to prevent repeated log warnings or timeouts
_MISTRAL_EMBEDDING_SUPPORTED = True

def _local_hash_vectorizer(text):
    """
    Fallback vectorizer: L2-normalized 128-dimensional term frequency mapping.
    Uses polynomial feature hashing to guarantee deterministic and package-free vector matching.
    """
    if not text:
        return [0.0] * 128
        
    # Preprocess text (lowercase and tokenize)
    words = text.lower().replace('\n', ' ').replace('\r', ' ').split()
    vector = [0.0] * 128
    
    # Feature hashing
    for word in words:
        # Polynomial rolling hash
        h = 0
        for char in word:
            h = (h * 31 + ord(char)) % 128
        vector[h] += 1.0
        
    # L2 Normalization
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [v / magnitude for v in vector]
        
    return vector

def get_embedding(text):
    """
    Fetches embedding from local Mistral server, falling back to local hash vectorizer if unavailable.
    """
    global _MISTRAL_EMBEDDING_SUPPORTED
    
    if not _MISTRAL_EMBEDDING_SUPPORTED:
        return _local_hash_vectorizer(text)
        
    url_ollama = f"{MISTRAL_LOCAL_URL}/api/embeddings"
    headers = {"Content-Type": "application/json"}
    payload_ollama = {
        "model": MISTRAL_LOCAL_MODEL,
        "prompt": text
    }
    
    try:
        res = requests.post(url_ollama, json=payload_ollama, headers=headers, timeout=60)
        if res.status_code == 200:
            data = res.json()
            embedding = data.get("embedding")
            if embedding:
                return embedding
    except Exception:
        pass

    url_openai = f"{MISTRAL_LOCAL_URL}/v1/embeddings"
    payload_openai = {
        "model": MISTRAL_LOCAL_MODEL,
        "input": text
    }
    
    try:
        res = requests.post(url_openai, json=payload_openai, headers=headers, timeout=60)
        if res.status_code == 200:
            data = res.json()
            embedding = data.get("data", [{}])[0].get("embedding")
            if embedding:
                return embedding
        elif res.status_code == 501:
            print("Mistral embedding failed with status 501. Caching hash-vector fallback.")
            _MISTRAL_EMBEDDING_SUPPORTED = False
    except Exception as e:
        # Silently degrade to hash vectorizer and log warning
        print(f"Error querying Mistral embedding endpoint. Falling back to local vectorizer. Error: {e}")
        
    return _local_hash_vectorizer(text)

import chromadb

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path="./chroma_store")

def get_chroma_collection(collection_name):
    # Use cosine distance for similarity matching
    return chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

def store_embedding(collection_name, doc_id, text, metadata=None):
    """Stores text, its embedding, and metadata in a ChromaDB collection."""
    collection = get_chroma_collection(collection_name)
    embedding = get_embedding(text)
    
    collection.upsert(
        ids=[str(doc_id)],
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata] if metadata else [{}]
    )
    return True

def search_embeddings(collection_name, query, n_results=3):
    """Searches the ChromaDB collection for the nearest neighbors to the query."""
    collection = get_chroma_collection(collection_name)
    query_emb = get_embedding(query)
    
    try:
        results = collection.query(
            query_embeddings=[query_emb],
            n_results=n_results
        )
        
        parsed_results = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                # Chroma returns cosine distance. Similarity = 1 - distance
                distance = results["distances"][0][i] if "distances" in results else 0
                similarity = 1.0 - distance
                
                parsed_results.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i] if "documents" in results else "",
                    "metadata": results["metadatas"][0][i] if "metadatas" in results else {},
                    "similarity": similarity
                })
        return parsed_results
    except Exception as e:
        print(f"Error querying ChromaDB collection {collection_name}: {e}")
        return []

def cosine_similarity(vec1, vec2):
    """
    Calculates cosine similarity between two numeric lists.
    Kept for legacy compatibility.
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    if mag1 == 0.0 or mag2 == 0.0:
        return 0.0
    return dot_product / (mag1 * mag2)

def retrieve_nearest(query, candidates, top_n=3):
    """
    Legacy method for in-memory searching over a list of candidate dictionaries.
    """
    query_emb = get_embedding(query)
    scored = []
    
    for c in candidates:
        emb = c.get("embedding")
        if not emb:
            name = c.get("name", "")
            desc = c.get("description", "")
            emb = get_embedding(f"{name} {desc}")
            c["embedding"] = emb
            
        sim = cosine_similarity(query_emb, emb)
        scored.append((sim, c))
        
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:top_n]]
