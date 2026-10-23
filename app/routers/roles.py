from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import commit_or_conflict
from app.models.role import (
    Role,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    StaffRoleLink,
)

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
    responses={409: {"description": "Unique-value or relationship conflict"}},
)


def get_role_or_404(role_id: int, session: Session) -> Role:
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.post(
    "",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a role",
)
def create_role(
    role: RoleCreate,
    session: Annotated[Session, Depends(get_session)],
) -> Role:
    if session.exec(select(Role).where(Role.name == role.name)).first():
        raise HTTPException(status_code=409, detail="Role name already exists")
    db_role = Role.model_validate(role)
    session.add(db_role)
    commit_or_conflict(session)
    session.refresh(db_role)
    return db_role


@router.get("", response_model=list[RoleRead], summary="List roles")
def list_roles(
    session: Annotated[Session, Depends(get_session)],
) -> list[Role]:
    return list(session.exec(select(Role)).all())


@router.get(
    "/{role_id}",
    response_model=RoleRead,
    summary="Get a role",
    responses={404: {"description": "Role not found"}},
)
def get_role(
    role_id: Annotated[
        int,
        Path(gt=0, description="ID of the role record.", examples=[1]),
    ],
    session: Annotated[Session, Depends(get_session)],
) -> Role:
    return get_role_or_404(role_id, session)


@router.patch(
    "/{role_id}",
    response_model=RoleRead,
    summary="Update a role",
    responses={404: {"description": "Role not found"}},
)
def update_role(
    role_id: Annotated[
        int,
        Path(
            gt=0,
            description="ID of the role record to update.",
            examples=[1],
        ),
    ],
    changes: RoleUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> Role:
    role = get_role_or_404(role_id, session)
    data = changes.model_dump(exclude_unset=True)
    if (
        data.get("name")
        and session.exec(
            select(Role).where(Role.name == data["name"], Role.id != role_id),
        ).first()
    ):
        raise HTTPException(status_code=409, detail="Role name already exists")
    role.sqlmodel_update(data)
    session.add(role)
    commit_or_conflict(session)
    session.refresh(role)
    return role


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a role",
    responses={404: {"description": "Role not found"}},
)
def delete_role(
    role_id: Annotated[
        int,
        Path(gt=0, description="ID of the role record.", examples=[1]),
    ],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    role = get_role_or_404(role_id, session)
    if (
        session.exec(
            select(StaffRoleLink.staff_id).where(
                StaffRoleLink.role_id == role_id,
            ),
        ).first()
        is not None
    ):
        raise HTTPException(
            status_code=409,
            detail="Role is assigned to staff; remove assignments first",
        )
    session.delete(role)
    commit_or_conflict(session)
