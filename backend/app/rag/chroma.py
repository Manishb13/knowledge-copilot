import os
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "chroma_db")
TOP_K_DEFAULT = int(os.getenv("TOP_K_RESULTS", "5"))

_chroma_client = None


def _get_client() -> chromadb.PersistentClient:
    """Return a singleton ChromaDB persistent client."""
    global _chroma_client
    if _chroma_client is None:
        Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
    return _chroma_client


def _collection_name(corpus_id: int, user_id: int) -> str:
    """Generate a unique ChromaDB collection name for a corpus."""
    return f"user_{user_id}_corpus_{corpus_id}"


def create_corpus_collection(corpus_id: int, user_id: int) -> chromadb.Collection:
    """
    Create a ChromaDB collection for a corpus.
    If the collection already exists, return it.
    """
    client = _get_client()
    name = _collection_name(corpus_id, user_id)
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def delete_corpus_collection(corpus_id: int, user_id: int) -> None:
    """Delete the ChromaDB collection for a corpus, if it exists."""
    client = _get_client()
    name = _collection_name(corpus_id, user_id)
    try:
        client.delete_collection(name=name)
    except Exception:
        pass


def store_chunks(
    corpus_id: int,
    user_id: int,
    chunks: List[dict],
    embeddings: List[List[float]],
    filename: str,
) -> None:
    """
    Store document chunks and their embeddings into the ChromaDB collection.

    Args:
        corpus_id: The corpus identifier.
        user_id: The user identifier.
        chunks: List of chunk dicts with keys: chunk_id, text, page_number, chunk_index.
        embeddings: Corresponding list of embedding vectors.
        filename: Original filename of the uploaded document.
    """
    client = _get_client()
    name = _collection_name(corpus_id, user_id)
    collection = client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [chunk["chunk_id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "chunk_text": chunk["text"],
            "filename": filename,
            "page_number": chunk["page_number"] if chunk["page_number"] is not None else -1,
            "chunk_id": chunk["chunk_id"],
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in chunks
    ]

    batch_size = 500
    for i in range(0, len(ids), batch_size):
        collection.add(
            ids=ids[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
            documents=documents[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )


def retrieve_chunks(
    corpus_id: int,
    user_id: int,
    query_embedding: List[float],
    top_k: int = TOP_K_DEFAULT,
) -> List[dict]:
    """
    Retrieve the top-k most similar chunks from ChromaDB.

    Args:
        corpus_id: The corpus to search.
        user_id: The owning user.
        query_embedding: The embedding vector for the user's question.
        top_k: Number of results to return.

    Returns:
        List of dicts with keys: chunk_id, chunk_text, filename, page_number, distance.
    """
    client = _get_client()
    name = _collection_name(corpus_id, user_id)

    try:
        collection = client.get_collection(name=name)
    except Exception:
        return []

    count = collection.count()
    if count == 0:
        return []

    actual_top_k = min(top_k, count)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=actual_top_k,
        include=["metadatas", "distances", "documents"],
    )

    retrieved: List[dict] = []
    if not results["metadatas"] or not results["metadatas"][0]:
        return []

    for i, metadata in enumerate(results["metadatas"][0]):
        page_num = metadata.get("page_number", -1)
        retrieved.append({
            "chunk_id": metadata.get("chunk_id", ""),
            "chunk_text": metadata.get("chunk_text", results["documents"][0][i]),
            "filename": metadata.get("filename", "unknown"),
            "page_number": page_num if page_num != -1 else None,
            "distance": results["distances"][0][i] if results["distances"] else 0.0,
        })

    return retrieved
