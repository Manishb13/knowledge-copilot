import json
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user_id
from app.database import get_db
from app.models import rows_to_list, parse_citations
from app.rag.chroma import retrieve_chunks
from app.rag.embeddings import generate_embeddings
from app.rag.generator import generate_answer
from app.schemas import Citation, ChatMessage, QueryRequest, QueryResponse

router = APIRouter()

HISTORY_TURNS = 5


def _verify_corpus_ownership(cursor: sqlite3.Cursor, corpus_id: int, user_id: int) -> None:
    """Raise 404 if corpus doesn't exist or doesn't belong to the user."""
    row = cursor.execute(
        "SELECT id FROM corpora WHERE id = ? AND user_id = ?",
        (corpus_id, user_id),
    ).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found",
        )


@router.post("/corpora/{corpus_id}/query", response_model=QueryResponse)
def query_corpus(
    corpus_id: int,
    payload: QueryRequest,
    db: sqlite3.Connection = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> QueryResponse:
    """Answer a natural-language question against a corpus using RAG."""
    cursor = db.cursor()
    _verify_corpus_ownership(cursor, corpus_id, user_id)

    history_rows = cursor.execute(
        """
        SELECT role, content FROM chat_messages
        WHERE corpus_id = ? AND user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (corpus_id, user_id, HISTORY_TURNS * 2),
    ).fetchall()

    conversation_history = list(reversed([
        {"role": row["role"], "content": row["content"]}
        for row in history_rows
    ]))

    try:
        query_embeddings = generate_embeddings([payload.question])
        query_embedding = query_embeddings[0]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate query embedding: {exc}",
        )

    try:
        retrieved_chunks = retrieve_chunks(
            corpus_id=corpus_id,
            user_id=user_id,
            query_embedding=query_embedding,
            top_k=int(5),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chunks: {exc}",
        )

    if not retrieved_chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No relevant content found in this corpus. Please upload documents first.",
        )

    try:
        answer, citations = generate_answer(
            question=payload.question,
            chunks=retrieved_chunks,
            conversation_history=conversation_history,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate answer: {exc}",
        )

    cursor.execute(
        "INSERT INTO chat_messages (corpus_id, user_id, role, content, citations) VALUES (?, ?, ?, ?, ?)",
        (corpus_id, user_id, "user", payload.question, None),
    )

    citations_json = json.dumps([c.model_dump() for c in citations])
    cursor.execute(
        "INSERT INTO chat_messages (corpus_id, user_id, role, content, citations) VALUES (?, ?, ?, ?, ?)",
        (corpus_id, user_id, "assistant", answer, citations_json),
    )
    db.commit()

    return QueryResponse(
        answer=answer,
        citations=citations,
        corpus_id=corpus_id,
    )


@router.get("/corpora/{corpus_id}/history", response_model=list[ChatMessage])
def get_chat_history(
    corpus_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[ChatMessage]:
    """Retrieve the full conversation history for a corpus."""
    cursor = db.cursor()
    _verify_corpus_ownership(cursor, corpus_id, user_id)

    rows = cursor.execute(
        """
        SELECT id, role, content, citations, created_at
        FROM chat_messages
        WHERE corpus_id = ? AND user_id = ?
        ORDER BY created_at ASC
        """,
        (corpus_id, user_id),
    ).fetchall()

    messages = []
    for row in rows:
        raw = dict(row)
        citations = [Citation(**c) for c in parse_citations(raw.get("citations"))]
        messages.append(
            ChatMessage(
                id=raw["id"],
                role=raw["role"],
                content=raw["content"],
                citations=citations,
                created_at=raw["created_at"],
            )
        )
    return messages


@router.delete("/corpora/{corpus_id}/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_chat_history(
    corpus_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """Clear all conversation history for a corpus."""
    cursor = db.cursor()
    _verify_corpus_ownership(cursor, corpus_id, user_id)

    cursor.execute(
        "DELETE FROM chat_messages WHERE corpus_id = ? AND user_id = ?",
        (corpus_id, user_id),
    )
    db.commit()
