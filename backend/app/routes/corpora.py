import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user_id
from app.database import get_db
from app.models import rows_to_list, row_to_dict
from app.rag.chroma import create_corpus_collection, delete_corpus_collection
from app.schemas import CorpusCreateRequest, CorpusListResponse, CorpusResponse

router = APIRouter()


@router.post("/corpora", response_model=CorpusResponse, status_code=status.HTTP_201_CREATED)
def create_corpus(
    payload: CorpusCreateRequest,
    db: sqlite3.Connection = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> CorpusResponse:
    """Create a new corpus for the authenticated user."""
    cursor = db.cursor()

    existing = cursor.execute(
        "SELECT id FROM corpora WHERE user_id = ? AND name = ?",
        (user_id, payload.name),
    ).fetchone()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A corpus named '{payload.name}' already exists",
        )

    cursor.execute(
        "INSERT INTO corpora (user_id, name, description) VALUES (?, ?, ?)",
        (user_id, payload.name, payload.description),
    )
    db.commit()
    corpus_id = cursor.lastrowid

    create_corpus_collection(corpus_id=corpus_id, user_id=user_id)

    row = cursor.execute(
        "SELECT * FROM corpora WHERE id = ?", (corpus_id,)
    ).fetchone()

    data = row_to_dict(row)
    return CorpusResponse(**data)


@router.get("/corpora", response_model=CorpusListResponse)
def list_corpora(
    db: sqlite3.Connection = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> CorpusListResponse:
    """List all corpora owned by the authenticated user."""
    cursor = db.cursor()

    rows = cursor.execute(
        "SELECT * FROM corpora WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()

    corpora = [CorpusResponse(**row_to_dict(r)) for r in rows]
    return CorpusListResponse(corpora=corpora)


@router.delete("/corpora/{corpus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_corpus(
    corpus_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """Delete a corpus and all its associated data."""
    cursor = db.cursor()

    row = cursor.execute(
        "SELECT id FROM corpora WHERE id = ? AND user_id = ?",
        (corpus_id, user_id),
    ).fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found",
        )

    delete_corpus_collection(corpus_id=corpus_id, user_id=user_id)

    cursor.execute("DELETE FROM corpora WHERE id = ?", (corpus_id,))
    db.commit()
