"""Shared database transaction handling."""

from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

if TYPE_CHECKING:
    from sqlmodel import Session

CONFLICT_DETAIL = "Operation conflicts with an existing record or relationship"


def commit_or_conflict(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=CONFLICT_DETAIL,
        ) from exc
