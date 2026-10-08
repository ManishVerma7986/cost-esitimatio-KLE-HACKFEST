"""FastAPI dependency injection utilities."""

from __future__ import annotations

import uuid
from typing import Generator, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models.user import User
from app.db.session import SessionLocal
from app.security.auth import decode_access_token

security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and safely close it on completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db),
) -> User:
    """Retrieve current authenticated user from JWT token, or default user in dev."""
    settings = get_settings()

    if credentials and credentials.credentials:
        token = credentials.credentials
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if user_id:
                user = db.execute(
                    select(User).where(User.id == uuid.UUID(user_id))
                ).scalar_one_or_none()
                if user and user.is_active:
                    return user
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials or token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # In development mode, ensure a default local dev user exists
    if not settings.is_production:
        dev_email = settings.dev_user_email
        dev_user = db.execute(
            select(User).where(User.email == dev_email)
        ).scalar_one_or_none()
        if not dev_user:
            from app.security.auth import get_password_hash
            dev_user = User(
                id=uuid.uuid4(),
                email=dev_email,
                full_name="Lead Project Architect",
                hashed_password=get_password_hash(settings.dev_user_password),
                is_active=True,
            )
            db.add(dev_user)
            db.commit()
            db.refresh(dev_user)
        return dev_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
