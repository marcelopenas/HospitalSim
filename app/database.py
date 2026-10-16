from collections.abc import Generator
import os

from sqlmodel import Session, SQLModel, create_engine


DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL, echo=os.getenv("SQL_ECHO", "").lower() == "true")


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
