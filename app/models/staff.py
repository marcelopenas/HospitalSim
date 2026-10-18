from typing import TYPE_CHECKING

from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.hospital import Hospital
    from app.models.patient import Patient
    from app.models.role import Role


class StaffBase(SQLModel):
    first_name: str = Field(min_length=1, max_length=100, description="Staff member's given name.", schema_extra={"examples": ["Olivia"]})
    last_name: str = Field(min_length=1, max_length=100, description="Staff member's family name.", schema_extra={"examples": ["Chen"]})
    hospital_id: int = Field(foreign_key="hospital.id", description="ID of an existing hospital; transfers require no assigned patients.", schema_extra={"examples": [1]})


class Staff(StaffBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    hospital: Hospital = Relationship(
        sa_relationship=relationship("Hospital", back_populates="staff"),
    )
    patients: list[Patient] = Relationship(
        sa_relationship=relationship("Patient", back_populates="staff", passive_deletes="all"),
    )
    roles: list[Role] = Relationship(
        sa_relationship=relationship(
            "Role", secondary="staff_roles", back_populates="staff"
        ),
    )


class StaffCreate(StaffBase):
    role_ids: list[int] = Field(default_factory=list, description="Existing role IDs. [] clears roles; omission or null in PATCH retains them.", schema_extra={"examples": [[1]]})


class StaffRead(StaffBase):
    id: int
    role_ids: list[int] = Field(default_factory=list, description="Existing role IDs. [] clears roles; omission or null in PATCH retains them.", schema_extra={"examples": [[1]]})


class StaffUpdate(SQLModel):
    first_name: str = Field(default=None, min_length=1, max_length=100, description="Staff member's given name. Omit in PATCH to retain the value; null is rejected.", schema_extra={"examples": ["Olivia"]})
    last_name: str = Field(default=None, min_length=1, max_length=100, description="Staff member's family name. Omit in PATCH to retain the value; null is rejected.", schema_extra={"examples": ["Chen"]})
    hospital_id: int = Field(default=None, foreign_key="hospital.id", description="ID of an existing hospital; transfers require no assigned patients. Omit in PATCH to retain the value; null is rejected.", schema_extra={"examples": [1]})
    role_ids: list[int] | None = Field(default=None, description="Existing role IDs. [] clears roles; omission or null in PATCH retains them.", schema_extra={"examples": [[1]]})
