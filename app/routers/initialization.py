from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.dialects.mysql import insert
from sqlmodel import Session

from app.database import get_session
from app.dependencies import commit_or_conflict
from app.models.application_state import ApplicationState, InitializationRead

router = APIRouter(prefix="/initialization", tags=["Application"])


@router.get("", response_model=InitializationRead, summary="Check dashboard initialization")
def get_initialization(
    session: Annotated[Session, Depends(get_session)],
) -> InitializationRead:
    state = session.get(ApplicationState, 1)
    return InitializationRead(was_initialized=state.was_initialized if state else False)


@router.post(
    "", response_model=InitializationRead, summary="Complete dashboard initialization",
    description="Idempotently remember that the startup choice completed. This does not populate or delete domain records. Only resetting the database clears the flag.",
)
def complete_initialization(
    session: Annotated[Session, Depends(get_session)],
) -> InitializationRead:
    statement = insert(ApplicationState).values(id=1, was_initialized=True)
    session.exec(statement.on_duplicate_key_update(was_initialized=True))
    commit_or_conflict(session)
    return InitializationRead(was_initialized=True)
