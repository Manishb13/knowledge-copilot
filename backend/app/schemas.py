from typing import Any, Optional
from pydantic import BaseModel, EmailStr, field_validator


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


# ─── Corpus Schemas ───────────────────────────────────────────────────────────

class CorpusCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Corpus name cannot be empty")
        return v


class CorpusResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    created_at: str


class CorpusListResponse(BaseModel):
    corpora: list[CorpusResponse]


# ─── Document Schemas ─────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: int
    corpus_id: int
    filename: str
    original_filename: str
    file_type: str
    chunk_count: int
    uploaded_at: str


class UploadResponse(BaseModel):
    message: str
    document: DocumentResponse


# ─── Citation Schema ──────────────────────────────────────────────────────────

class Citation(BaseModel):
    chunk_id: str
    filename: str
    page_number: Optional[int]
    chunk_text: str


# ─── Query Schemas ────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        return v


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    corpus_id: int


# ─── Chat History Schema ──────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    id: int
    role: str
    content: str
    citations: list[Citation]
    created_at: str
