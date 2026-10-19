import base64
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from pydantic import field_validator
from sqlalchemy import LargeBinary
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

from app.images import DEFAULT_IMAGE, MAX_BASE64_LENGTH, validate_image

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
    image_blob: bytes = Field(default=DEFAULT_IMAGE, sa_type=LargeBinary(), nullable=False)
    id: int | None = Field(default=None, primary_key=True)

    staff: Staff | None = Relationship(
        sa_relationship=relationship("Staff", back_populates="patients"),
    )
    hospital: Hospital = Relationship(
        sa_relationship=relationship("Hospital", back_populates="patients"),
    )


class PatientCreate(PatientBase):
    image_blob: str | None = Field(default=None, max_length=MAX_BASE64_LENGTH, description="Base64-encoded PNG, JPEG, or WebP, at most 65535 decoded bytes. Omit or null for the default profile icon; do not include a data-URL prefix.", schema_extra={"examples": [base64.b64encode(DEFAULT_IMAGE).decode("ascii")]})
    _image = field_validator("image_blob")(validate_image)


class PatientRead(PatientBase):
    id: int
    image_blob: str = Field(description="Image BLOB encoded as base64 (PNG, JPEG, or WebP), without a data-URL prefix.")


class PatientUpdate(SQLModel):
    image_blob: str | None = Field(default=None, max_length=MAX_BASE64_LENGTH, description="Base64 image, at most 65535 decoded bytes. Omit to retain the image; null restores the default profile icon.", schema_extra={"examples": [None]})
    _image = field_validator("image_blob")(validate_image)
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
