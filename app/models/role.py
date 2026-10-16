from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.staff import Staff


class StaffRoleLink(SQLModel, table=True):
    __tablename__ = "staff_roles"

    staff_id: int = Field(foreign_key="staff.id", primary_key=True)
    role_id: int = Field(foreign_key="role.id", primary_key=True)


class RoleBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class Role(RoleBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    staff: list[Staff] = Relationship(
        back_populates="roles",
        link_model=StaffRoleLink,
    )


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase):
    id: int


class RoleUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
