from typing import Optional
from fastapi import APIRouter, HTTPException, Response, Depends
from app.models import (
    User,
    Organization,
    UserOrganizationRole,
    UserRole,
)
from app.database import get_db_session
from starlette.requests import Request
from app.schemas import OrganizationsResponse
from uuid import UUID
from sqlmodel import Session


router = APIRouter()


@router.get("/", tags=["organizations"], response_model=list[Organization])
async def user_organizations(
    request: Request,
) -> OrganizationsResponse:
    user: User = request.state.user
    return user.organizations


@router.get(
    "/{organization_id}",
    tags=["organizations"],
    response_model=Organization,
)
async def organizations(
    request: Request, organization_id: UUID, db: Session = Depends(get_db_session)
) -> Organization | None:
    user: User = request.state.user

    organization: Optional[Organization] = next(
        (org for org in user.organizations if org.id == organization_id), None
    )

    if organization is None:
        # unauthorized
        raise HTTPException(status_code=401, detail="Organization not found")
    return organization


@router.get("/{organization_id}/members", tags=["organizations", "members"])
async def organization_members(
    request: Request, organization_id: UUID, db: Session = Depends(get_db_session)
) -> list[User | None]:
    user: User = request.state.user

    organization: Optional[Organization] = next(
        (org for org in user.organizations if org.id == organization_id), None
    )

    if organization is None:
        # unauthorized
        raise HTTPException(status_code=401, detail="Organization not found")

    return organization.members


@router.post("/", tags=["organizations"], response_model=Organization)
async def create_organization(
    request: Request, name: str, db: Session = Depends(get_db_session)
) -> Organization | Response:
    user: User = request.state.user
    try:
        db.begin()
        organization = Organization(name=name, owner=user.id)
        db.add(organization)
        db.commit()
        user_organization = UserOrganizationRole(
            user_id=user.id, organization_id=organization.id, user_role=UserRole.creator
        )
        db.add(user_organization)
        db.commit()
        db.refresh(organization)
    except:
        db.rollback()
        raise
    return organization


@router.delete("/{organization_id}", tags=["organizations"])
async def delete_organization(request: Request, organization_id: UUID) -> Response:
    user: User = request.state.user
    db = request.state.db
    organization: Optional[Organization] = next(
        (org for org in user.organizations if org.id == organization_id), None
    )
    if organization is None:
        raise HTTPException(status_code=401, detail="Organization not found")
    if organization.owner != user.id:
        raise HTTPException(
            status_code=401, detail="User is not the owner of the organization"
        )
    try:
        db.delete(organization)
        db.commit()
    except:
        db.rollback()
        raise
    return Response(status_code=204)
