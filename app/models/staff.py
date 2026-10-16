from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.role import StaffRoleLink

if TYPE_CHECKING:
    from app.models.hospital import Hospital
    from app.models.patient import Patient
    from app.models.role import Role


class StaffBase(SQLModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    hospital_id: int = Field(foreign_key="hospital.id")


class Staff(StaffBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    hospital: "Hospital" = Relationship(back_populates="staff")
    patients: list["Patient"] = Relationship(back_populates="staff")
    roles: list["Role"] = Relationship(
        back_populates="staff", link_model=StaffRoleLink
    )


class StaffCreate(StaffBase):
    role_ids: list[int] = Field(default_factory=list)


class StaffRead(StaffBase):
    id: int
    role_ids: list[int] = Field(default_factory=list)


class StaffUpdate(SQLModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    hospital_id: int | None = Field(default=None, foreign_key="hospital.id")
    role_ids: list[int] | None = None
