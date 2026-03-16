"""Embedding engine using Ollama qwen3-embedding and ChromaDB."""
import requests
import chromadb
import json
import os
from config import OLLAMA_BASE_URL, EMBEDDING_MODEL, CHROMA_DB_PATH


def get_chroma_client():
    """Get ChromaDB persistent client."""
    return chromadb.PersistentClient(path=CHROMA_DB_PATH)


def get_or_create_collection(collection_name="medical_reports"):
    """Get or create a ChromaDB collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


def generate_embedding(text):
    """Generate embedding using Ollama qwen3-embedding model."""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={
                "model": EMBEDDING_MODEL,
                "input": text
            },
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        # Ollama /api/embed returns {"embeddings": [[...]]}
        if "embeddings" in data and len(data["embeddings"]) > 0:
            return data["embeddings"][0]
        # Fallback for older API format
        if "embedding" in data:
            return data["embedding"]
        return None
    except Exception as e:
        print(f"Embedding error: {e}")
        return None


def embed_document(report_id, patient_id, text_chunks, metadata=None):
    """Embed document chunks into ChromaDB."""
    collection = get_or_create_collection()

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(text_chunks):
        if not chunk.strip():
            continue

        embedding = generate_embedding(chunk)
        if embedding is None:
            continue

        doc_id = f"report_{report_id}_chunk_{i}"
        ids.append(doc_id)
        embeddings.append(embedding)
        documents.append(chunk)
        metadatas.append({
            "report_id": str(report_id),
            "patient_id": str(patient_id),
            "chunk_index": i,
            **(metadata or {})
        })

    if ids:
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    return len(ids)


def query_similar(query_text, patient_id=None, n_results=5):
    """Query ChromaDB for similar documents."""
    collection = get_or_create_collection()

    query_embedding = generate_embedding(query_text)
    if query_embedding is None:
        return []

    where_filter = None
    if patient_id:
        where_filter = {"patient_id": str(patient_id)}

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )

        docs = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                docs.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0
                })
        return docs
    except Exception as e:
        print(f"Query error: {e}")
        return []


def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks."""
    chunks = []
    words = text.split()
    if not words:
        return [text] if text.strip() else []

    current_chunk = []
    current_length = 0

    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1

        if current_length >= chunk_size:
            chunks.append(" ".join(current_chunk))
            # Keep overlap
            overlap_words = current_chunk[-overlap // 5:] if len(current_chunk) > overlap // 5 else []
            current_chunk = overlap_words
            current_length = sum(len(w) + 1 for w in current_chunk)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
