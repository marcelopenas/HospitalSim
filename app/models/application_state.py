"""Database-wide dashboard onboarding state, separate from domain records."""

from sqlmodel import Field, SQLModel


class ApplicationState(SQLModel, table=True):
    __tablename__ = "app_state"

    id: int = Field(default=1, primary_key=True)
    was_initialized: bool = Field(default=False)


class InitializationRead(SQLModel):
    was_initialized: bool = Field(
        description="Whether the empty/populate startup choice has been completed for this database.",
    )
