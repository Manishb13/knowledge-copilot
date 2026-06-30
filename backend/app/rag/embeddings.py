import os
from typing import List

from openai import OpenAI

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Return a singleton OpenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=api_key)
    return _client


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text strings using OpenAI's embedding model.
    Processes texts in batches to stay within API limits.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each a list of floats).
    """
    if not texts:
        return []

    client = _get_client()
    all_embeddings: List[List[float]] = []

    cleaned_texts = [text.replace("\n", " ").strip() for text in texts]
    cleaned_texts = [t if t else " " for t in cleaned_texts]

    for i in range(0, len(cleaned_texts), EMBEDDING_BATCH_SIZE):
        batch = cleaned_texts[i : i + EMBEDDING_BATCH_SIZE]
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings
