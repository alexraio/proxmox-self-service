"""Authentication endpoints: register, login, me.

Shared FastAPI dependencies (get_current_user, require_admin) are also
exported from here so other routers can import them without circular imports.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.utils import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models import User
from app.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter()
_bearer = HTTPBearer()


# ── Shared dependencies ───────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: decode JWT and return the authenticated User.

    Args:
        credentials: Bearer token extracted from the Authorization header.
        db: Injected database session.

    Returns:
        User: The ORM User instance matching the token subject.

    Raises:
        HTTPException 401: Token is missing, invalid, or expired.
        HTTPException 404: User referenced in the token no longer exists.
    """
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: int = int(payload["sub"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido o scaduto.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato."
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: ensure the current user has admin privileges.

    Args:
        current_user: Authenticated user from ``get_current_user``.

    Returns:
        User: The admin User instance.

    Raises:
        HTTPException 403: User is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso riservato agli amministratori.",
        )
    return current_user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    payload: UserRegisterRequest, db: Session = Depends(get_db)
) -> UserResponse:
    """Register a new user account.

    Args:
        payload: Registration data (username, email, password).
        db: Injected database session.

    Returns:
        UserResponse: Newly created user (without password hash).

    Raises:
        HTTPException 409: Username or email already in use.
    """
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username già in uso.")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email già registrata.")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate a user and return a JWT access token.

    Args:
        payload: Login credentials (username, password).
        db: Injected database session.

    Returns:
        TokenResponse: Signed JWT and user profile.

    Raises:
        HTTPException 401: Credentials are invalid.
    """
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide.",
        )
    token = create_access_token(
        subject=user.id, username=user.username, is_admin=user.is_admin
    )
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user's public profile.

    Args:
        current_user: Authenticated user from JWT (injected).

    Returns:
        UserResponse: Current user's public profile.
    """
    return current_user
