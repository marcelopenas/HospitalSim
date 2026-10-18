import os
from typing import TYPE_CHECKING

from sqlalchemy.engine import make_url
from sqlmodel import Session, SQLModel, create_engine

if TYPE_CHECKING:
    from collections.abc import Generator

DATABASE_URL = os.environ["DATABASE_URL"]
if make_url(DATABASE_URL).drivername != "mysql+pymysql":
    msg = "DATABASE_URL must use mysql+pymysql; MySQL is the only supported database"
    raise ValueError(msg)

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "").lower() == "true",
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
