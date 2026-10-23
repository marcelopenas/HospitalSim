from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from pydantic import field_serializer, field_validator
from sqlalchemy import CheckConstraint, Numeric
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from decimal import Decimal

    from app.models.hospital import Hospital
    from app.models.patient import Patient
    from app.models.role import Role


class StaffBase(SQLModel):
    first_name: str = Field(
        min_length=1,
        max_length=100,
        description="Staff member's given name.",
        schema_extra={"examples": ["Olivia"]},
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
        description="Staff member's family name.",
        schema_extra={"examples": ["Chen"]},
    )
    hospital_id: int = Field(
        foreign_key="hospital.id",
        description="ID of an existing hospital; transfers require no assigned patients.",
        schema_extra={"examples": [1]},
    )
    date_of_admission: date = Field(
        description="Date this staff member joined the hospital (DATE, no time).",
        schema_extra={"examples": ["2024-01-15"]},
    )
    last_check_in: datetime | None = Field(
        default=None,
        sa_type=DATETIME(fsp=6),
        description="Last check-in time, stored as UTC DATETIME without a time-zone suffix. Offset inputs are converted to UTC; null means no check-in.",
        schema_extra={"examples": ["2026-01-12T08:30:00"]},
    )
    salary: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2,
        sa_type=Numeric(12, 2),
        description="Non-negative exact monetary amount (DECIMAL(12,2)); send a decimal string to preserve cents. Currency and pay period are not prescribed.",
        schema_extra={"examples": ["7500.00"]},
    )

    @field_validator("last_check_in")
    @classmethod
    def check_in_in_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is not None:
            return value.astimezone(UTC).replace(tzinfo=None)
        return value

    @field_serializer("salary", when_used="json-unless-none")
    def serialize_salary(self, value: Decimal) -> str:
        return format(value, ".2f")


class Staff(StaffBase, table=True):
    __table_args__ = (CheckConstraint("salary >= 0", name="ck_staff_salary"),)
    id: int | None = Field(default=None, primary_key=True)

    hospital: Hospital = Relationship(
        sa_relationship=relationship("Hospital", back_populates="staff"),
    )
    patients: list[Patient] = Relationship(
        sa_relationship=relationship(
            "Patient",
            back_populates="staff",
            passive_deletes="all",
        ),
    )
    roles: list[Role] = Relationship(
        sa_relationship=relationship(
            "Role",
            secondary="staff_roles",
            back_populates="staff",
        ),
    )


class StaffCreate(StaffBase):
    role_ids: list[int] = Field(
        default_factory=list,
        description="Existing role IDs. [] clears roles; omission or null in PATCH retains them.",
        schema_extra={"examples": [[1]]},
    )


class StaffRead(StaffBase):
    id: int
    role_ids: list[int] = Field(
        default_factory=list,
        description="Existing role IDs. [] clears roles; omission or null in PATCH retains them.",
        schema_extra={"examples": [[1]]},
    )


class StaffUpdate(SQLModel):
    first_name: str = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Staff member's given name. Omit in PATCH to retain the value; null is rejected.",
        schema_extra={"examples": ["Olivia"]},
    )
    last_name: str = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Staff member's family name. Omit in PATCH to retain the value; null is rejected.",
        schema_extra={"examples": ["Chen"]},
    )
    hospital_id: int = Field(
        default=None,
        foreign_key="hospital.id",
        description="ID of an existing hospital; transfers require no assigned patients. Omit in PATCH to retain the value; null is rejected.",
        schema_extra={"examples": [1]},
    )
    role_ids: list[int] | None = Field(
        default=None,
        description="Existing role IDs. [] clears roles; omission or null in PATCH retains them.",
        schema_extra={"examples": [[1]]},
    )

    date_of_admission: date = Field(
        default=None,
        description="Admission date (YYYY-MM-DD), without time. Omit to retain; null is rejected.",
        schema_extra={"examples": ["2024-01-15"]},
    )
    last_check_in: datetime | None = Field(
        default=None,
        description="UTC check-in DATETIME; offset inputs are converted to UTC. Null clears it; omission retains it.",
        schema_extra={"examples": ["2026-01-12T08:30:00"]},
    )
    salary: Decimal = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Exact monetary amount, up to 9999999999.99. Send a decimal string; omit to retain; null is rejected.",
        schema_extra={"examples": ["7500.00"]},
    )

    @field_validator("last_check_in")
    @classmethod
    def check_in_in_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is not None:
            return value.astimezone(UTC).replace(tzinfo=None)
        return value

    @field_serializer("salary", when_used="json-unless-none")
    def serialize_salary(self, value: Decimal) -> str:
        return format(value, ".2f")
