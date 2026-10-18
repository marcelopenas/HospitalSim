from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.staff import Staff


class StaffRoleLink(SQLModel, table=True):
    __tablename__ = "staff_roles"

    staff_id: int = Field(foreign_key="staff.id", primary_key=True)
    role_id: int = Field(foreign_key="role.id", primary_key=True)


class RoleBase(SQLModel):
    name: str = Field(unique=True, min_length=1, max_length=100, description="Unique occupation label; does not grant access permissions.", schema_extra={"examples": ["Physician"]})
    description: str | None = Field(default=None, max_length=500, description="Optional role description; null clears it.", schema_extra={"examples": ["Provides patient care"]})


class Role(RoleBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    staff: list[Staff] = Relationship(
        sa_relationship=relationship(
            "Staff", secondary="staff_roles", back_populates="roles", passive_deletes=True
        ),
    )


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase):
    id: int


class RoleUpdate(SQLModel):
    name: str = Field(default=None, min_length=1, max_length=100, description="Unique occupation label; does not grant access permissions. Omit in PATCH to retain the value; null is rejected.", schema_extra={"examples": ["Physician"]})
    description: str | None = Field(default=None, max_length=500, description="Optional role description; null clears it.", schema_extra={"examples": ["Provides patient care"]})
