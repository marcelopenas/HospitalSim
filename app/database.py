import os
from typing import TYPE_CHECKING

from sqlmodel import Session, SQLModel, create_engine

if TYPE_CHECKING:
    from collections.abc import Generator

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "").lower() == "true",
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
