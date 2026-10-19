import base64
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlmodel import Session, func, select

from app.database import get_session
from app.dependencies import commit_or_conflict
from app.images import decode_image
from app.models.hospital import Hospital
from app.models.patient import (
    Patient,
    PatientCreate,
    PatientRead,
    PatientUpdate,
)
from app.models.staff import Staff

router = APIRouter(prefix="/patients", tags=["Patients"], responses={409: {"description": "Unique-value or relationship conflict"}})


def validate_patient_references(
    hospital_id: int,
    staff_id: int | None,
    session: Session,
    patient_id: int | None = None,
) -> None:
    hospital = session.exec(select(Hospital).where(Hospital.id == hospital_id).with_for_update()).first()
    if hospital is None:
        raise HTTPException(status_code=400, detail="Hospital not found")
    if staff_id is not None:
        staff = session.get(Staff, staff_id)
        if staff is None:
            raise HTTPException(
                status_code=400,
                detail="Staff member not found",
            )
        if staff.hospital_id != hospital_id:
            raise HTTPException(
                status_code=400,
                detail="staff_id and hospital_id must refer to the same hospital",
            )

    count_query = select(func.count()).select_from(Patient).where(Patient.hospital_id == hospital_id)
    if patient_id is not None:
        count_query = count_query.where(Patient.id != patient_id)
    if session.exec(count_query).one() >= hospital.capacity:
        raise HTTPException(status_code=409, detail="Hospital capacity reached; choose another hospital or increase capacity")


def to_read(patient: Patient) -> PatientRead:
    return PatientRead.model_validate({**patient.model_dump(), "image_blob": base64.b64encode(patient.image_blob).decode("ascii")})


def get_patient_or_404(patient_id: int, session: Session, *, lock: bool = False) -> Patient:
    query = select(Patient).where(Patient.id == patient_id)
    patient = session.exec(query.with_for_update() if lock else query).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post(
    "",
    response_model=PatientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a patient",
    description="Create a patient and optionally assign a staff member.",
)
def create_patient(
    patient: PatientCreate,
    session: Annotated[Session, Depends(get_session)],
) -> PatientRead:
    validate_patient_references(patient.hospital_id, patient.staff_id, session)
    db_patient = Patient.model_validate(patient, update={"image_blob": decode_image(patient.image_blob)})
    session.add(db_patient)
    commit_or_conflict(session)
    session.refresh(db_patient)
    return to_read(db_patient)


@router.get("", response_model=list[PatientRead], summary="List patients")
def list_patients(
    session: Annotated[Session, Depends(get_session)],
) -> list[PatientRead]:
    return [to_read(patient) for patient in session.exec(select(Patient)).all()]


@router.get(
    "/{patient_id}",
    response_model=PatientRead,
    summary="Get a patient",
    responses={404: {"description": "Patient not found"}},
)
def get_patient(
    patient_id: Annotated[int, Path(gt=0, description="ID of the patient record.", examples=[1])],
    session: Annotated[Session, Depends(get_session)],
) -> PatientRead:
    return to_read(get_patient_or_404(patient_id, session))


@router.patch(
    "/{patient_id}",
    response_model=PatientRead,
    summary="Update a patient",
    responses={404: {"description": "Patient not found"}},
)
def update_patient(
    patient_id: Annotated[int, Path(gt=0, description="ID of the patient record to update.", examples=[1])],
    changes: PatientUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> PatientRead:
    patient = get_patient_or_404(patient_id, session, lock=True)
    data = changes.model_dump(exclude_unset=True)
    hospital_id = data.get("hospital_id", patient.hospital_id)
    staff_id = data.get("staff_id", patient.staff_id)
    validate_patient_references(hospital_id, staff_id, session, patient_id)
    if "image_blob" in data:
        data["image_blob"] = decode_image(data["image_blob"])
    patient.sqlmodel_update(data)
    session.add(patient)
    commit_or_conflict(session)
    session.refresh(patient)
    return to_read(patient)


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a patient",
    responses={404: {"description": "Patient not found"}},
)
def delete_patient(
    patient_id: Annotated[int, Path(gt=0, description="ID of the patient record.", examples=[1])],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    patient = get_patient_or_404(patient_id, session, lock=True)
    session.delete(patient)
    commit_or_conflict(session)
