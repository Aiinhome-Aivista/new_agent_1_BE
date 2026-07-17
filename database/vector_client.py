import os
import requests
import json
import math
from dotenv import load_dotenv

load_dotenv()

MISTRAL_LOCAL_URL = os.getenv("MISTRAL_LOCAL_URL", "http://122.163.121.176:3041").rstrip('/')
MISTRAL_LOCAL_MODEL = os.getenv("MISTRAL_LOCAL_MODEL", "mistral-small:24b")

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
        
    url = f"{MISTRAL_LOCAL_URL}/v1/embeddings"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": MISTRAL_LOCAL_MODEL,
        "input": text
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=5)
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

def cosine_similarity(vec1, vec2):
    """
    Calculates cosine similarity between two numeric lists.
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
    Ranks candidates by cosine similarity against the query embedding.
    candidates list should consist of dicts with 'embedding' key.
    """
    query_emb = get_embedding(query)
    scored = []
    
    for c in candidates:
        emb = c.get("embedding")
        # Generate embedding dynamically if missing
        if not emb:
            name = c.get("name", "")
            desc = c.get("description", "")
            emb = get_embedding(f"{name} {desc}")
            c["embedding"] = emb
            
        sim = cosine_similarity(query_emb, emb)
        scored.append((sim, c))
        
    # Sort descending
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:top_n]]
