import os
import sqlite3
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.auth import get_current_user_id
from app.database import get_db
from app.models import row_to_dict
from app.rag.chunker import chunk_text
from app.rag.embeddings import generate_embeddings
from app.rag.chroma import store_chunks
from app.rag.parser import parse_document
from app.schemas import DocumentResponse, UploadResponse

router = APIRouter()

UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", "uploads"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def _verify_corpus_ownership(cursor: sqlite3.Cursor, corpus_id: int, user_id: int) -> None:
    """Raise 404 if the corpus doesn't exist or doesn't belong to the user."""
    row = cursor.execute(
        "SELECT id FROM corpora WHERE id = ? AND user_id = ?",
        (corpus_id, user_id),
    ).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found",
        )


@router.post("/corpora/{corpus_id}/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    corpus_id: int,
    file: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> UploadResponse:
    """Upload a document to a corpus: parse, chunk, embed, and index it."""
    cursor = db.cursor()
    _verify_corpus_ownership(cursor, corpus_id, user_id)

    original_filename = file.filename or "unknown"
    suffix = Path(original_filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed size of {MAX_FILE_SIZE_MB} MB",
        )

    corpus_upload_dir = UPLOADS_DIR / str(user_id) / str(corpus_id)
    corpus_upload_dir.mkdir(parents=True, exist_ok=True)

    unique_filename = f"{uuid.uuid4().hex}{suffix}"
    file_path = corpus_upload_dir / unique_filename

    file_path.write_bytes(content)

    try:
        chunks = parse_document(file_path=file_path, original_filename=original_filename)
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse document: {exc}",
        )

    if not chunks:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No text content could be extracted from the document",
        )

    text_chunks = chunk_text(chunks)

    try:
        embeddings = generate_embeddings([c["text"] for c in text_chunks])
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate embeddings: {exc}",
        )

    try:
        store_chunks(
            corpus_id=corpus_id,
            user_id=user_id,
            chunks=text_chunks,
            embeddings=embeddings,
            filename=original_filename,
        )
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store vectors: {exc}",
        )

    cursor.execute(
        """
        INSERT INTO documents (corpus_id, filename, original_filename, file_type, file_path, chunk_count)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            corpus_id,
            unique_filename,
            original_filename,
            suffix.lstrip("."),
            str(file_path),
            len(text_chunks),
        ),
    )
    db.commit()
    doc_id = cursor.lastrowid

    row = cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    doc_data = row_to_dict(row)

    return UploadResponse(
        message=f"Document '{original_filename}' uploaded and indexed successfully",
        document=DocumentResponse(**doc_data),
    )
