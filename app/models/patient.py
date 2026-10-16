from datetime import date
from typing import TYPE_CHECKING, Optional

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
        if value >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return value


class Patient(PatientBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    staff: Optional["Staff"] = Relationship(back_populates="patients")
    hospital: "Hospital" = Relationship(back_populates="patients")


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
        if value is not None and value >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return value