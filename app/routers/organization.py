from typing import Optional
from fastapi import APIRouter, HTTPException
from app.models import User, Organization
from app.database import get_db
from starlette.requests import Request
from app.schemas import OrganizationsResponse
from uuid import UUID
from sqlmodel import select

router = APIRouter()


@router.get(
    "/organization", tags=["organization"], response_model=OrganizationsResponse
)
async def user_organizations(
    request: Request,
) -> OrganizationsResponse:

    user: User = request.state.get_user(request, organizations=True)
    return OrganizationsResponse(organizations=user.organizations)


@router.get(
    "/organization/{organization_id}",
    tags=["organization"],
    response_model=Organization,
)
async def organization(request: Request, organization_id: UUID) -> Organization | None:
    user: User = request.state.get_user(request, organizations=True)

    organization: Optional[Organization] = next(
        (org for org in user.organizations if org.id == organization_id), None
    )

    if organization is None:
        # unauthorized
        raise HTTPException(status_code=401, detail="Organization not found")
    return organization


# @router.get("/organization/{organization_id}/members", tags=["organization"])
# async def organization_members(request: Request, organization_id: UUID) -> list[User]:
#     user: User = request.state.get_user(request, organizations=True)

#     organization: Optional[Organization] = next(
#         (org for org in user.organizations if org.id == organization_id), None
#     )

#     if organization is None:
#         # unauthorized
#         raise HTTPException(status_code=401, detail="Organization not found")
#     organization


#     return organization.members
