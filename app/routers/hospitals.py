from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlmodel import Session, func, select

from app.database import get_session
from app.dependencies import commit_or_conflict
from app.models.hospital import (
    Hospital,
    HospitalCreate,
    HospitalRead,
    HospitalUpdate,
)
from app.models.patient import Patient
from app.models.staff import Staff

router = APIRouter(
    prefix="/hospitals",
    tags=["Hospitals"],
    responses={409: {"description": "Unique-value or relationship conflict"}},
)


@router.post(
    "",
    response_model=HospitalRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a hospital",
    description="Create a hospital with a unique name and location.",
)
def create_hospital(
    hospital: HospitalCreate,
    session: Annotated[Session, Depends(get_session)],
) -> Hospital:
    if session.exec(
        select(Hospital).where(
            (Hospital.name == hospital.name)
            | (Hospital.location == hospital.location),
        ),
    ).first():
        raise HTTPException(
            status_code=409,
            detail="Hospital name or location already exists",
        )
    db_hospital = Hospital.model_validate(hospital)
    session.add(db_hospital)
    commit_or_conflict(session)
    session.refresh(db_hospital)
    return db_hospital


@router.get(
    "",
    response_model=list[HospitalRead],
    summary="List hospitals",
    description="Return all hospitals.",
)
def list_hospitals(
    session: Annotated[Session, Depends(get_session)],
) -> list[Hospital]:
    return list(session.exec(select(Hospital)).all())


@router.get(
    "/{hospital_id}",
    response_model=HospitalRead,
    summary="Get a hospital",
    responses={404: {"description": "Hospital not found"}},
)
def get_hospital(
    hospital_id: Annotated[
        int, Path(gt=0, description="ID of the hospital record.", examples=[1])
    ],
    session: Annotated[Session, Depends(get_session)],
) -> Hospital:
    hospital = session.get(Hospital, hospital_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital


@router.patch(
    "/{hospital_id}",
    response_model=HospitalRead,
    summary="Update a hospital",
    responses={404: {"description": "Hospital not found"}},
)
def update_hospital(
    hospital_id: Annotated[
        int,
        Path(
            gt=0,
            description="ID of the hospital record to update.",
            examples=[1],
        ),
    ],
    changes: HospitalUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> Hospital:
    hospital = session.exec(
        select(Hospital).where(Hospital.id == hospital_id).with_for_update(),
    ).first()
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")
    data = changes.model_dump(exclude_unset=True)
    if (
        data
        and session.exec(
            select(Hospital).where(
                Hospital.id != hospital_id,
                (Hospital.name == data.get("name", hospital.name))
                | (
                    Hospital.location
                    == data.get("location", hospital.location)
                ),
            ),
        ).first()
    ):
        raise HTTPException(
            status_code=409,
            detail="Hospital name or location already exists",
        )
    if "capacity" in data:
        count = session.exec(
            select(func.count())
            .select_from(Patient)
            .where(Patient.hospital_id == hospital_id),
        ).one()
        if data["capacity"] < count:
            raise HTTPException(
                status_code=409,
                detail="Capacity cannot be lower than the patient count",
            )
    hospital.sqlmodel_update(data)
    session.add(hospital)
    commit_or_conflict(session)
    session.refresh(hospital)
    return hospital


@router.delete(
    "/{hospital_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a hospital",
    responses={404: {"description": "Hospital not found"}},
)
def delete_hospital(
    hospital_id: Annotated[
        int,
        Path(gt=0, description="ID of the hospital record.", examples=[1]),
    ],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    hospital = session.get(Hospital, hospital_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")
    if (
        session.exec(
            select(Staff.id).where(Staff.hospital_id == hospital_id),
        ).first()
        is not None
        or session.exec(
            select(Patient.id).where(Patient.hospital_id == hospital_id),
        ).first()
        is not None
    ):
        raise HTTPException(
            status_code=409,
            detail="Hospital has staff or patients; remove dependents first",
        )
    session.delete(hospital)
    commit_or_conflict(session)
