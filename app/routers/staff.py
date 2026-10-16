from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, col, select

from app.database import get_session
from app.models.hospital import Hospital
from app.models.role import Role
from app.models.staff import Staff, StaffCreate, StaffRead, StaffUpdate

router = APIRouter(prefix="/staff", tags=["Staff"])


def get_staff_or_404(staff_id: int, session: Session) -> Staff:
    staff = session.get(Staff, staff_id)
    if staff is None:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return staff


def validate_references(
    hospital_id: int,
    role_ids: list[int],
    session: Session,
) -> list[Role]:
    if session.get(Hospital, hospital_id) is None:
        raise HTTPException(status_code=400, detail="Hospital not found")

    roles = list(
        session.exec(select(Role).where(col(Role.id).in_(role_ids))).all(),
    )

    if len(roles) != len(set(role_ids)):
        raise HTTPException(
            status_code=400,
            detail="One or more roles were not found",
        )
    return roles


def to_read(staff: Staff) -> StaffRead:
    assert staff.id is not None, "Staff ID cannot be None for read models"  # noqa: S101

    return StaffRead(
        id=staff.id,
        first_name=staff.first_name,
        last_name=staff.last_name,
        hospital_id=staff.hospital_id,
        role_ids=sorted(
            role.id for role in staff.roles if role.id is not None
        ),
    )


@router.post(
    "",
    response_model=StaffRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a staff member",
    description="Create staff and optionally assign multiple roles.",
)
def create_staff(
    staff: StaffCreate,
    session: Annotated[Session, Depends(get_session)],
) -> StaffRead:
    roles = validate_references(staff.hospital_id, staff.role_ids, session)
    db_staff = Staff.model_validate(staff, update={"roles": roles})
    session.add(db_staff)
    session.commit()
    session.refresh(db_staff)
    return to_read(db_staff)


@router.get("", response_model=list[StaffRead], summary="List staff members")
def list_staff(
    session: Annotated[Session, Depends(get_session)],
) -> list[StaffRead]:
    return [to_read(staff) for staff in session.exec(select(Staff)).all()]


@router.get(
    "/{staff_id}",
    response_model=StaffRead,
    summary="Get a staff member",
    responses={404: {"description": "Staff member not found"}},
)
def get_staff(
    staff_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> StaffRead:
    return to_read(get_staff_or_404(staff_id, session))


@router.patch(
    "/{staff_id}",
    response_model=StaffRead,
    summary="Update a staff member",
    responses={404: {"description": "Staff member not found"}},
)
def update_staff(
    staff_id: int,
    changes: StaffUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> StaffRead:
    staff = get_staff_or_404(staff_id, session)
    data = changes.model_dump(exclude_unset=True)
    role_ids = data.pop("role_ids", None)
    hospital_id = data.get("hospital_id", staff.hospital_id)
    roles = (
        validate_references(hospital_id, role_ids or [], session)
        if role_ids is not None
        else None
    )
    staff.sqlmodel_update(data)
    if roles is not None:
        staff.roles = roles
    session.add(staff)
    session.commit()
    session.refresh(staff)
    return to_read(staff)


@router.delete(
    "/{staff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a staff member",
    responses={404: {"description": "Staff member not found"}},
)
def delete_staff(
    staff_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> None:
    staff = get_staff_or_404(staff_id, session)
    session.delete(staff)
    session.commit()
