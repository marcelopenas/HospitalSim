from typing import TYPE_CHECKING, Literal

from sqlalchemy import CHAR, CheckConstraint
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.staff import Staff


class StaffRoleLink(SQLModel, table=True):
    __tablename__ = "staff_roles"

    staff_id: int = Field(foreign_key="staff.id", primary_key=True)
    role_id: int = Field(foreign_key="role.id", primary_key=True)


class RoleBase(SQLModel):
    name: str = Field(unique=True, min_length=1, max_length=100, description="Unique occupation or responsibility label.", schema_extra={"examples": ["Physician"]})
    description: str | None = Field(default=None, max_length=500, description="Optional role description; null clears it.", schema_extra={"examples": ["Provides patient care"]})

    access_type: Literal["A", "B", "C"] = Field(sa_type=CHAR(1), description="Hospital access classification: A, B, or C. Metadata only; the API has no authentication.", schema_extra={"examples": ["A"]})


class Role(RoleBase, table=True):
    __table_args__ = (CheckConstraint("access_type IN ('A', 'B', 'C')", name="ck_role_access_type"),)
    id: int | None = Field(default=None, primary_key=True)

    # The native collection annotation prevents shared roles being inferred as scalar.
    staff: list[Staff] = Relationship(
        sa_relationship=relationship(
            "Staff", secondary="staff_roles", back_populates="roles", passive_deletes=True,
            uselist=True,
        ),
    )


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase):
    id: int


class RoleUpdate(SQLModel):
    name: str = Field(default=None, min_length=1, max_length=100, description="Unique occupation or responsibility label. Omit in PATCH to retain the value; null is rejected.", schema_extra={"examples": ["Physician"]})
    description: str | None = Field(default=None, max_length=500, description="Optional role description; null clears it.", schema_extra={"examples": ["Provides patient care"]})

    access_type: Literal["A", "B", "C"] = Field(default=None, description="One-character hospital access classification. Omit to retain; null is rejected.", schema_extra={"examples": ["B"]})
