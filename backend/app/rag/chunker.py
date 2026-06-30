import os
import uuid
from typing import Optional

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))


def _split_text_into_chunks(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Split text into overlapping chunks using character-based sliding window.
    Attempts to split on sentence/paragraph boundaries within the chunk.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            chunk = text[start:]
            if chunk.strip():
                chunks.append(chunk.strip())
            break

        boundary = -1
        for sep in ["\n\n", "\n", ". ", "! ", "? ", "; "]:
            pos = text.rfind(sep, start, end)
            if pos != -1 and pos > start:
                boundary = pos + len(sep)
                break

        if boundary == -1 or boundary <= start:
            boundary = end

        chunk = text[start:boundary]
        if chunk.strip():
            chunks.append(chunk.strip())

        start = max(start + 1, boundary - chunk_overlap)

    return chunks


def chunk_text(pages: list[dict]) -> list[dict]:
    """
    Take a list of page dicts {text, page_number} and return a flat list
    of chunk dicts with unique IDs and metadata.

    Returns:
        List of dicts with keys:
            - chunk_id: str (UUID)
            - text: str
            - page_number: int | None
            - chunk_index: int (sequential across all chunks)
    """
    all_chunks: list[dict] = []
    chunk_index = 0

    for page in pages:
        page_text: str = page.get("text", "")
        page_number: Optional[int] = page.get("page_number")

        if not page_text.strip():
            continue

        text_chunks = _split_text_into_chunks(page_text, CHUNK_SIZE, CHUNK_OVERLAP)

        for chunk_text_content in text_chunks:
            if not chunk_text_content.strip():
                continue

            all_chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "text": chunk_text_content,
                "page_number": page_number,
                "chunk_index": chunk_index,
            })
            chunk_index += 1

    return all_chunks
