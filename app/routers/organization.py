from typing import Optional
from fastapi import APIRouter, HTTPException, Response, Depends
from app.models import User, Organization, UserOrganization, UserRole
from app.database import get_db, get_db_session
from starlette.requests import Request
from app.schemas import OrganizationsResponse
from uuid import UUID
from sqlmodel import Session
from sqlalchemy.orm import joinedload

router = APIRouter()


@router.get(
    "/organization", tags=["organization"], response_model=OrganizationsResponse
)
async def user_organizations(
        request: Request,
) -> OrganizationsResponse:
    user: User = request.state.user
    return OrganizationsResponse(organizations=user.organizations)


@router.get(
    "/organization/{organization_id}",
    tags=["organization"],
    response_model=Organization,
)
async def organization(request: Request, organization_id: UUID,
                       db: Session = Depends(get_db_session)) -> Organization | None:
    user: User = request.state.user

    organization: Optional[Organization] = next(
        (org for org in user.organizations if org.id == organization_id), None
    )

    if organization is None:
        # unauthorized
        raise HTTPException(status_code=401, detail="Organization not found")
    return organization


@router.get("/organization/{organization_id}/members", tags=["organization"])
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

    organization = db.get(
        Organization, organization_id, options=[joinedload(Organization.members)]
    )

    return organization.members


@router.post("/organization", tags=["organization"], response_model=Organization)
async def create_organization(request: Request, name: str,
                              db: Session = Depends(get_db_session)) -> Organization | Response:
    user: User = request.state.user
    try:
        db.begin()
        organization = Organization(name=name, owner=user.id)
        db.add(organization)
        db.commit()
        user_organization = UserOrganization(user_id=user.id, organization_id=organization.id,
                                             user_role=UserRole.creator)
        db.add(user_organization)
        db.commit()
    except:
        db.rollback()
        raise
    print(organization.name, organization.owner)
    return organization
