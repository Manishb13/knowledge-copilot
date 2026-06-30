import os
from typing import List, Tuple

from openai import OpenAI

from app.schemas import Citation

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1500"))

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


def _build_context_block(chunks: List[dict]) -> str:
    """Format retrieved chunks into a context block for the prompt."""
    lines = []
    for i, chunk in enumerate(chunks, 1):
        page_info = f" (Page {chunk['page_number']})" if chunk.get("page_number") else ""
        lines.append(
            f"[SOURCE {i}] File: {chunk['filename']}{page_info}\n"
            f"{chunk['chunk_text']}\n"
        )
    return "\n---\n".join(lines)


SYSTEM_PROMPT = """You are a precise and helpful domain knowledge assistant.

You answer questions strictly based on the provided source passages.

Rules:
1. Base your answer ONLY on the provided source passages.
2. If the answer cannot be found in the passages, say "I could not find information about this in the provided documents."
3. Always cite your sources by referencing [SOURCE N] inline in your answer.
4. Be concise and accurate.
5. Do not fabricate information.
6. When quoting or paraphrasing, always include the source reference like [SOURCE 1] or [SOURCE 2].
"""


def generate_answer(
    question: str,
    chunks: List[dict],
    conversation_history: List[dict],
) -> Tuple[str, List[Citation]]:
    """
    Generate an answer using OpenAI with retrieved chunks as context.

    Args:
        question: The user's question.
        chunks: Retrieved document chunks with metadata.
        conversation_history: Previous conversation turns (list of {role, content}).

    Returns:
        Tuple of (answer_text, list_of_citations).
    """
    client = _get_client()
    context_block = _build_context_block(chunks)

    user_message = (
        f"SOURCE PASSAGES:\n\n{context_block}\n\n"
        f"QUESTION: {question}\n\n"
        f"Answer based on the source passages above and cite sources inline using [SOURCE N]."
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=0.1,
    )

    answer_text = response.choices[0].message.content or ""

    citations = _extract_citations(answer_text, chunks)

    return answer_text, citations


def _extract_citations(answer_text: str, chunks: List[dict]) -> List[Citation]:
    """
    Parse [SOURCE N] references from the answer text and build Citation objects
    for each referenced chunk.

    Args:
        answer_text: The generated answer containing [SOURCE N] references.
        chunks: The list of retrieved chunks (1-indexed in the answer).

    Returns:
        List of Citation objects for all sources actually referenced in the answer.
    """
    import re

    referenced_indices = set(
        int(m) for m in re.findall(r"\[SOURCE (\d+)\]", answer_text, re.IGNORECASE)
    )

    if not referenced_indices:
        return [
            Citation(
                chunk_id=chunk["chunk_id"],
                filename=chunk["filename"],
                page_number=chunk.get("page_number"),
                chunk_text=chunk["chunk_text"],
            )
            for chunk in chunks[:3]
        ]

    citations: List[Citation] = []
    seen_chunk_ids = set()

    for idx in sorted(referenced_indices):
        chunk_index = idx - 1
        if 0 <= chunk_index < len(chunks):
            chunk = chunks[chunk_index]
            if chunk["chunk_id"] not in seen_chunk_ids:
                seen_chunk_ids.add(chunk["chunk_id"])
                citations.append(
                    Citation(
                        chunk_id=chunk["chunk_id"],
                        filename=chunk["filename"],
                        page_number=chunk.get("page_number"),
                        chunk_text=chunk["chunk_text"],
                    )
                )

    return citations
