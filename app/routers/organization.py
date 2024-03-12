import select
from typing import Optional
from fastapi import APIRouter, Body, HTTPException, Response, Depends
from app.models import (
    User,
    Organization,
    UserOrganizationRole,
    UserRole,
    Invitation,
    InvitationStatus,
)
from app.database import get_db_session
from starlette.requests import Request
from app.schemas import OrganizationsResponse, OrganizationInvitationRequest
from uuid import UUID
from sqlmodel import Session, select, and_
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
async def organization(
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

    return organization.members


@router.post("/organization", tags=["organization"], response_model=Organization)
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


@router.delete("/organization/{organization_id}", tags=["organization"])
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


@router.post("/organization/{organization_id}/invitation", tags=["organization"])
async def invite_member(
    request: Request,
    organization_id: UUID,
    invitation: OrganizationInvitationRequest = Body(...),
    db: Session = Depends(get_db_session),
) -> Response:

    # current user can invite to organization
    user: User = request.state.user
    organization: Optional[Organization] = next(
        (org for org in user.organizations if org.id == organization_id), None
    )
    if organization is None:
        raise HTTPException(status_code=401, detail="Organization not found")

    current_user_role: UserOrganizationRole = db.exec(
        select(UserOrganizationRole)
        .where(UserOrganizationRole.user_id == user.id)
        .where(UserOrganizationRole.organization_id == organization_id)
    ).first()
    if current_user_role.user_role == UserRole.staff or (
        current_user_role.user_role == UserRole.admin
        and invitation.role in [UserRole.creator, UserRole.admin]
    ):
        raise HTTPException(
            status_code=401,
            detail="User is not authorized to invite members with this role",
        )

    invited_user: User = db.exec(
        select(User).where(User.email == invitation.email)
    ).first()
    if invited_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # check if user is already a member of the organization
    user_organization_role: UserOrganizationRole = db.exec(
        select(UserOrganizationRole)
        .where(UserOrganizationRole.user_id == invited_user.id)
        .where(UserOrganizationRole.organization_id == organization_id)
    ).first()

    if user_organization_role is not None:
        raise HTTPException(
            status_code=400, detail="User is already a member of the organization"
        )

    # check if user has already been invited to the organization with the same role
    user_invitation: Invitation = db.exec(
        select(Invitation)
        .where(Invitation.user_id == invited_user.id)
        .where(Invitation.organization_id == organization_id)
        .where(Invitation.role == invitation.role)
        .where(Invitation.inviter_id == user.id)
    ).first()

    if user_invitation is not None:
        if user_invitation.role == invitation.role:
            raise HTTPException(
                status_code=400,
                detail="User has already been invited to the organization with the same role",
            )

    # TODO fix default value for role and status

    user_invitation = Invitation(
        user_id=invited_user.id,
        organization_id=organization_id,
        inviter_id=user.id,
        role=invitation.role,
        status=InvitationStatus.pending,
    )

    try:
        db.add(user_invitation)
        db.commit()
        # TODO send email to invited user with invitation link
    except:
        db.rollback()
        raise
    return Response(status_code=201)
