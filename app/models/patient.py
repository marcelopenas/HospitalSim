from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.hospital import Hospital
    from app.models.staff import Staff


class PatientBase(SQLModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    staff_id: int | None = Field(default=None, foreign_key="staff.id")
    hospital_id: int = Field(foreign_key="hospital.id")

    @field_validator("date_of_birth")
    @classmethod
    def date_must_be_in_the_past(cls, value: date) -> date:
        if value >= datetime.now(tz=UTC).date():
            msg = "date_of_birth must be in the past"
            raise ValueError(msg)
        return value


class Patient(PatientBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    staff: Staff | None = Relationship(back_populates="patients")
    hospital: Hospital = Relationship(back_populates="patients")


class PatientCreate(PatientBase):
    pass


class PatientRead(PatientBase):
    id: int


class PatientUpdate(SQLModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    staff_id: int | None = Field(default=None, foreign_key="staff.id")
    hospital_id: int | None = Field(default=None, foreign_key="hospital.id")

    @field_validator("date_of_birth")
    @classmethod
    def date_must_be_in_the_past(cls, value: date | None) -> date | None:
        if (
            value is not None
            and value >= datetime.now(tz=UTC).date()
        ):
            msg = "date_of_birth must be in the past"
            raise ValueError(msg)
        return value
