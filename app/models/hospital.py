from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.staff import Staff


class HospitalBase(SQLModel):
    name: str = Field(min_length=1, max_length=200, description="Unique hospital name.", schema_extra={"examples": ["Riverside Medical Center"]})
    location: str = Field(min_length=1, max_length=500, description="Unique free-text hospital location.", schema_extra={"examples": ["Boston, Massachusetts"]})


class Hospital(HospitalBase, table=True):
    __table_args__ = (
        UniqueConstraint("name", name="uq_hospital_name"),
        UniqueConstraint("location", name="uq_hospital_location"),
    )

    id: int | None = Field(default=None, primary_key=True)
    staff: list[Staff] = Relationship(
        sa_relationship=relationship("Staff", back_populates="hospital", passive_deletes="all"),
    )
    patients: list[Patient] = Relationship(
        sa_relationship=relationship("Patient", back_populates="hospital", passive_deletes="all"),
    )


class HospitalCreate(HospitalBase):
    pass


class HospitalRead(HospitalBase):
    id: int


class HospitalUpdate(SQLModel):
    name: str = Field(default=None, min_length=1, max_length=200, description="Unique hospital name. Omit in PATCH to retain the value; null is rejected.", schema_extra={"examples": ["Riverside Medical Center"]})
    location: str = Field(default=None, min_length=1, max_length=500, description="Unique free-text hospital location. Omit in PATCH to retain the value; null is rejected.", schema_extra={"examples": ["Boston, Massachusetts"]})
