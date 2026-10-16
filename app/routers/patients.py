from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.hospital import Hospital
from app.models.patient import Patient, PatientCreate, PatientRead, PatientUpdate
from app.models.staff import Staff

router = APIRouter(prefix="/patients", tags=["Patients"])


def validate_patient_references(
    hospital_id: int, staff_id: int | None, session: Session
) -> None:
    if session.get(Hospital, hospital_id) is None:
        raise HTTPException(status_code=400, detail="Hospital not found")
    if staff_id is not None:
        staff = session.get(Staff, staff_id)
        if staff is None:
            raise HTTPException(status_code=400, detail="Staff member not found")
        if staff.hospital_id != hospital_id:
            raise HTTPException(
                status_code=400,
                detail="staff_id and hospital_id must refer to the same hospital",
            )


def get_patient_or_404(patient_id: int, session: Session) -> Patient:
    patient = session.get(Patient, patient_id)
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
    patient: PatientCreate, session: Session = Depends(get_session)
) -> Patient:
    validate_patient_references(patient.hospital_id, patient.staff_id, session)
    db_patient = Patient.model_validate(patient)
    session.add(db_patient)
    session.commit()
    session.refresh(db_patient)
    return db_patient


@router.get("", response_model=list[PatientRead], summary="List patients")
def list_patients(session: Session = Depends(get_session)) -> list[Patient]:
    return list(session.exec(select(Patient)).all())


@router.get(
    "/{patient_id}",
    response_model=PatientRead,
    summary="Get a patient",
    responses={404: {"description": "Patient not found"}},
)
def get_patient(patient_id: int, session: Session = Depends(get_session)) -> Patient:
    return get_patient_or_404(patient_id, session)


@router.patch(
    "/{patient_id}",
    response_model=PatientRead,
    summary="Update a patient",
    responses={404: {"description": "Patient not found"}},
)
def update_patient(
    patient_id: int,
    changes: PatientUpdate,
    session: Session = Depends(get_session),
) -> Patient:
    patient = get_patient_or_404(patient_id, session)
    data = changes.model_dump(exclude_unset=True)
    hospital_id = data.get("hospital_id", patient.hospital_id)
    staff_id = data.get("staff_id", patient.staff_id)
    validate_patient_references(hospital_id, staff_id, session)
    patient.sqlmodel_update(data)
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return patient


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a patient",
    responses={404: {"description": "Patient not found"}},
)
def delete_patient(patient_id: int, session: Session = Depends(get_session)) -> None:
    patient = get_patient_or_404(patient_id, session)
    session.delete(patient)
    session.commit()
