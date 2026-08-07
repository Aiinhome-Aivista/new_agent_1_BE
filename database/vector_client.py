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

def _local_hash_vectorizer(text, dimension=384):
    """
    Fallback vectorizer: L2-normalized term frequency mapping.
    Uses polynomial feature hashing to guarantee deterministic and package-free vector matching.
    """
    if not text:
        return [0.0] * dimension
        
    # Preprocess text (lowercase and tokenize)
    words = text.lower().replace('\n', ' ').replace('\r', ' ').split()
    vector = [0.0] * dimension
    
    # Feature hashing
    for word in words:
        # Polynomial rolling hash
        h = 0
        for char in word:
            h = (h * 31 + ord(char)) % dimension
        vector[h] += 1.0
        
    # L2 Normalization
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [v / magnitude for v in vector]
        
    return vector

def get_embedding(text, dimension=384):
    """
    Fetches embedding from local Mistral server, falling back to Chroma's default embedding function,
    and finally to a local hash vectorizer of the requested dimension if everything else fails.
    """
    global _MISTRAL_EMBEDDING_SUPPORTED
    
    if _MISTRAL_EMBEDDING_SUPPORTED:
        url_ollama = f"{MISTRAL_LOCAL_URL}/api/embeddings"
        headers = {"Content-Type": "application/json"}
        payload_ollama = {
            "model": MISTRAL_LOCAL_MODEL,
            "prompt": text
        }
        
        try:
            res = requests.post(url_ollama, json=payload_ollama, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                embedding = data.get("embedding")
                if embedding and len(embedding) == dimension:
                    return embedding
        except Exception:
            pass

        url_openai = f"{MISTRAL_LOCAL_URL}/v1/embeddings"
        payload_openai = {
            "model": MISTRAL_LOCAL_MODEL,
            "input": text
        }
        
        try:
            res = requests.post(url_openai, json=payload_openai, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                embedding = data.get("data", [{}])[0].get("embedding")
                if embedding and len(embedding) == dimension:
                    return embedding
            elif res.status_code == 501:
                print("Mistral embedding failed with status 501. Caching local fallback.")
                _MISTRAL_EMBEDDING_SUPPORTED = False
        except Exception as e:
            print(f"Error querying Mistral embedding endpoint: {e}")
            _MISTRAL_EMBEDDING_SUPPORTED = False
            
    # Fallback 1: Chroma's DefaultEmbeddingFunction (usually 384 dimensions)
    try:
        from chromadb.utils import embedding_functions
        default_ef = embedding_functions.DefaultEmbeddingFunction()
        embeddings = default_ef([text])
        if embeddings and len(embeddings[0]) == dimension:
            return embeddings[0]
    except Exception as ef:
        print(f"Chroma default embedding function failed: {ef}")

    # Fallback 2: Local Hash Vectorizer matching the expected dimension
    return _local_hash_vectorizer(text, dimension=dimension)

import chromadb

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path="./chroma_store")

def get_chroma_collection(collection_name):
    # Use cosine distance for similarity matching
    return chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

def get_collection_dimension(collection):
    """Detects expected dimension of the collection from existing items or the embedding function."""
    # 1. Try to get sample from existing documents
    try:
        sample = collection.get(limit=1, include=["embeddings"])
        if sample is not None and sample.get("embeddings") is not None and len(sample["embeddings"]) > 0:
            return len(sample["embeddings"][0])
    except Exception:
        pass

    # 2. Try to get from embedding function
    try:
        if hasattr(collection, "_embedding_function") and collection._embedding_function is not None:
            test_emb = collection._embedding_function(["test"])
            if test_emb and len(test_emb[0]) > 0:
                return len(test_emb[0])
    except Exception:
        pass

    # 3. Default fallback
    return 384

def chunk_text(text, chunk_size=300, overlap=50):
    """Splits text into chunks of `chunk_size` words with an overlap of `overlap` words."""
    words = text.split()
    chunks = []
    if not words:
        return chunks
        
    if len(words) <= chunk_size:
        return [text]
        
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def store_embedding(collection_name, doc_id, text, metadata=None):
    """Stores text by chunking it, getting embeddings for each chunk, and storing in a ChromaDB collection with metadata."""
    collection = get_chroma_collection(collection_name)
    dimension = get_collection_dimension(collection)
    
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    if not chunks:
        return False
        
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    for idx, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{idx}"
        emb = get_embedding(chunk, dimension=dimension)
        
        chunk_meta = metadata.copy() if metadata else {}
        chunk_meta["chunk_index"] = idx
        chunk_meta["parent_doc_id"] = str(doc_id)
        
        ids.append(chunk_id)
        embeddings.append(emb)
        documents.append(chunk)
        metadatas.append(chunk_meta)
        
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    return True

def search_embeddings(collection_name, query, n_results=3):
    """Searches the ChromaDB collection for the nearest neighbors to the query."""
    collection = get_chroma_collection(collection_name)
    dimension = get_collection_dimension(collection)
    query_emb = get_embedding(query, dimension=dimension)
    
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
    # Detect candidate embedding dimension to match query
    dimension = 384
    for c in candidates:
        emb = c.get("embedding")
        if emb:
            dimension = len(emb)
            break
            
    query_emb = get_embedding(query, dimension=dimension)
    scored = []
    
    for c in candidates:
        emb = c.get("embedding")
        if not emb:
            name = c.get("name", "")
            desc = c.get("description", "")
            emb = get_embedding(f"{name} {desc}", dimension=dimension)
            c["embedding"] = emb
            
        sim = cosine_similarity(query_emb, emb)
        scored.append((sim, c))
        
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:top_n]]
