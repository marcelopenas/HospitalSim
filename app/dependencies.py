"""Shared database transaction handling."""
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session


def commit_or_conflict(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="Operation conflicts with an existing record or relationship") from exc
