from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.role import Role, RoleCreate, RoleRead, RoleUpdate

router = APIRouter(prefix="/roles", tags=["Roles"])


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
def create_role(role: RoleCreate, session: Session = Depends(get_session)) -> Role:
    if session.exec(select(Role).where(Role.name == role.name)).first():
        raise HTTPException(status_code=409, detail="Role name already exists")
    db_role = Role.model_validate(role)
    session.add(db_role)
    session.commit()
    session.refresh(db_role)
    return db_role


@router.get("", response_model=list[RoleRead], summary="List roles")
def list_roles(session: Session = Depends(get_session)) -> list[Role]:
    return list(session.exec(select(Role)).all())


@router.get(
    "/{role_id}",
    response_model=RoleRead,
    summary="Get a role",
    responses={404: {"description": "Role not found"}},
)
def get_role(role_id: int, session: Session = Depends(get_session)) -> Role:
    return get_role_or_404(role_id, session)


@router.patch(
    "/{role_id}",
    response_model=RoleRead,
    summary="Update a role",
    responses={404: {"description": "Role not found"}},
)
def update_role(
    role_id: int, changes: RoleUpdate, session: Session = Depends(get_session)
) -> Role:
    role = get_role_or_404(role_id, session)
    data = changes.model_dump(exclude_unset=True)
    if data.get("name") and session.exec(
        select(Role).where(Role.name == data["name"], Role.id != role_id)
    ).first():
        raise HTTPException(status_code=409, detail="Role name already exists")
    role.sqlmodel_update(data)
    session.add(role)
    session.commit()
    session.refresh(role)
    return role


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a role",
    responses={404: {"description": "Role not found"}},
)
def delete_role(role_id: int, session: Session = Depends(get_session)) -> None:
    role = get_role_or_404(role_id, session)
    session.delete(role)
    session.commit()
