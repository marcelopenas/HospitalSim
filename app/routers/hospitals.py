from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.hospital import Hospital, HospitalCreate, HospitalRead, HospitalUpdate

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.post(
    "",
    response_model=HospitalRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a hospital",
    description="Create a hospital with a unique name and location.",
)
def create_hospital(
    hospital: HospitalCreate, session: Session = Depends(get_session)
) -> Hospital:
    if session.exec(
        select(Hospital).where(
            (Hospital.name == hospital.name) | (Hospital.location == hospital.location)
        )
    ).first():
        raise HTTPException(status_code=409, detail="Hospital name or location already exists")
    db_hospital = Hospital.model_validate(hospital)
    session.add(db_hospital)
    session.commit()
    session.refresh(db_hospital)
    return db_hospital


@router.get(
    "",
    response_model=list[HospitalRead],
    summary="List hospitals",
    description="Return all hospitals.",
)
def list_hospitals(session: Session = Depends(get_session)) -> list[Hospital]:
    return list(session.exec(select(Hospital)).all())


@router.get(
    "/{hospital_id}",
    response_model=HospitalRead,
    summary="Get a hospital",
    responses={404: {"description": "Hospital not found"}},
)
def get_hospital(
    hospital_id: int, session: Session = Depends(get_session)
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
    hospital_id: int,
    changes: HospitalUpdate,
    session: Session = Depends(get_session),
) -> Hospital:
    hospital = session.get(Hospital, hospital_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")
    data = changes.model_dump(exclude_unset=True)
    if data and session.exec(
        select(Hospital).where(
            Hospital.id != hospital_id,
            (Hospital.name == data.get("name", hospital.name))
            | (Hospital.location == data.get("location", hospital.location)),
        )
    ).first():
        raise HTTPException(status_code=409, detail="Hospital name or location already exists")
    hospital.sqlmodel_update(data)
    session.add(hospital)
    session.commit()
    session.refresh(hospital)
    return hospital


@router.delete(
    "/{hospital_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a hospital",
    responses={404: {"description": "Hospital not found"}},
)
def delete_hospital(hospital_id: int, session: Session = Depends(get_session)) -> None:
    hospital = session.get(Hospital, hospital_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")
    session.delete(hospital)
    session.commit()
