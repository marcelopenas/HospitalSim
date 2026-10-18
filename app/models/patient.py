from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from pydantic import field_validator
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.hospital import Hospital
    from app.models.staff import Staff


class PatientBase(SQLModel):
    first_name: str = Field(min_length=1, max_length=100, description="Patient's given name.", schema_extra={"examples": ["Alex"]})
    last_name: str = Field(min_length=1, max_length=100, description="Patient's family name.", schema_extra={"examples": ["Taylor"]})
    date_of_birth: date = Field(description="Birth date before today's UTC date, in YYYY-MM-DD format.", schema_extra={"examples": ["1990-05-12"]})
    staff_id: int | None = Field(default=None, foreign_key="staff.id", description="Existing clinician at the same hospital; null unassigns the patient.", schema_extra={"examples": [1]})
    hospital_id: int = Field(foreign_key="hospital.id", description="ID of an existing hospital.", schema_extra={"examples": [1]})

    @field_validator("date_of_birth")
    @classmethod
    def date_must_be_in_the_past(cls, value: date) -> date:
        if value >= datetime.now(tz=UTC).date():
            msg = "date_of_birth must be in the past"
            raise ValueError(msg)
        return value


class Patient(PatientBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    staff: Staff | None = Relationship(
        sa_relationship=relationship("Staff", back_populates="patients"),
    )
    hospital: Hospital = Relationship(
        sa_relationship=relationship("Hospital", back_populates="patients"),
    )


class PatientCreate(PatientBase):
    pass


class PatientRead(PatientBase):
    id: int


class PatientUpdate(SQLModel):
    first_name: str = Field(default=None, min_length=1, max_length=100, description="Patient's given name. Omit in PATCH to retain the value; null is rejected.", schema_extra={"examples": ["Alex"]})
    last_name: str = Field(default=None, min_length=1, max_length=100, description="Patient's family name. Omit in PATCH to retain the value; null is rejected.", schema_extra={"examples": ["Taylor"]})
    date_of_birth: date = Field(default=None, description="Birth date before today's UTC date, in YYYY-MM-DD format. Omit in PATCH to retain the value; null is rejected.", schema_extra={"examples": ["1990-05-12"]})
    staff_id: int | None = Field(default=None, foreign_key="staff.id", description="Existing clinician at the same hospital; null unassigns the patient.", schema_extra={"examples": [1]})
    hospital_id: int = Field(default=None, foreign_key="hospital.id", description="ID of an existing hospital. Omit in PATCH to retain the value; null is rejected.", schema_extra={"examples": [1]})

    @field_validator("date_of_birth")
    @classmethod
    def date_must_be_in_the_past(cls, value: date) -> date:
        if value >= datetime.now(tz=UTC).date():
            msg = "date_of_birth must be in the past"
            raise ValueError(msg)
        return value
