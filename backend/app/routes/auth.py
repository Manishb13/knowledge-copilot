import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.schemas import LoginRequest, SignupRequest, TokenResponse

router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: sqlite3.Connection = Depends(get_db)) -> TokenResponse:
    """Register a new user and return a JWT access token."""
    cursor = db.cursor()

    existing = cursor.execute(
        "SELECT id FROM users WHERE email = ?", (payload.email,)
    ).fetchone()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    hashed = hash_password(payload.password)
    cursor.execute(
        "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
        (payload.email, hashed),
    )
    db.commit()

    user_id = cursor.lastrowid
    token = create_access_token(data={"sub": str(user_id)})

    return TokenResponse(
        access_token=token,
        user_id=user_id,
        email=payload.email,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: sqlite3.Connection = Depends(get_db)) -> TokenResponse:
    """Authenticate a user and return a JWT access token."""
    cursor = db.cursor()

    row = cursor.execute(
        "SELECT id, email, hashed_password FROM users WHERE email = ?",
        (payload.email,),
    ).fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(payload.password, row["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(data={"sub": str(row["id"])})

    return TokenResponse(
        access_token=token,
        user_id=row["id"],
        email=row["email"],
    )
