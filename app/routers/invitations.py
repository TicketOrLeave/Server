from os import getenv
from uuid import UUID
from sqlmodel import Session, select
from fastapi import APIRouter
from sqlalchemy.orm import joinedload
from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Response, Depends
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
from app.schemas import (
    OrganizationInvitationRequest,
    OrganizationInvitationResponse,
    Inviter,
    InvitedUser,
    UserInvitation,
    UserInvitationOrganization,
    InvitationStatusRequest,
)

from app.utilities.mail import EmailSender
from app.utilities.database import get_user_org_role, get_organization_by_user_id

router = APIRouter()
user_invitations_router = APIRouter()


@user_invitations_router.get(
    "/",
    tags=["invitations", "users"],
    response_model=list[UserInvitation],
)
async def get_user_invitations(
    request: Request,
    db: Session = Depends(get_db_session),
) -> list[UserInvitation]:
    """
    Get all invitations for the current user

    Args:
        request (Request): request object
        db (Session): database session

    Returns:
        list[UserInvitation]: list of user invitations
    """

    user: User = request.state.user
    invitations: list[Invitation] = user.invitations
    invitations_response: list[UserInvitation] = []
    for invitation in invitations:
        inviter = invitation.inviter
        organization = invitation.organization
        invitation_response = UserInvitation(
            id=invitation.id,
            status=invitation.status,
            created_at=invitation.created_at,
            updated_at=invitation.updated_at,
            inviter=Inviter(
                id=inviter.id,
                name=inviter.name,
                email=inviter.email,
            ),
            organization=UserInvitationOrganization(
                id=organization.id,
                name=organization.name,
            ),
        )
        invitations_response.append(invitation_response)

    return invitations_response


@user_invitations_router.put(
    "/{invitation_id}",
    tags=["invitations"],
)
async def invitation_status_update(
    request: Request,
    invitation_id: UUID,
    status_request: InvitationStatusRequest = Body(...),
    db: Session = Depends(get_db_session),
) -> Response:
    """
    Update invitation status

    Args:
        request (Request): request object
        invitation_id (UUID): invitation id
        status_request (InvitationStatusRequest): status request
        db (Session): database session

    Returns:
        Response: response object with status code 204
        HTTPException: 404 if invitation not found
        HTTPException: 500 if error updating invitation status
    """
    user: User = request.state.user
    invitation: Invitation | None = db.exec(
        select(Invitation)
        .where(Invitation.id == invitation_id)
        .where(Invitation.user_id == user.id)
    ).first()
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")

    invitation.status = status_request.status
    try:
        if status_request.status == InvitationStatus.accepted:
            user_organization_role = UserOrganizationRole(
                user_id=user.id,
                organization_id=invitation.organization_id,
                user_role=invitation.role,
            )
            db.add(user_organization_role)
            db.commit()
        elif status_request.status == InvitationStatus.rejected:
            db.delete(invitation)
            db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Invitation status update failed")
    return Response(status_code=204)


@router.post(
    "/",
    tags=["organizations", "invitations"],
)
async def invite_member(
    request: Request,
    organization_id: UUID,
    background: BackgroundTasks,
    invitation: OrganizationInvitationRequest = Body(...),
    db: Session = Depends(get_db_session),
) -> Response:
    """
    Invite a user to an organization

    Args:
        request (Request): request object
        organization_id (UUID): organization id
        background (BackgroundTasks): background tasks
        invitation (OrganizationInvitationRequest): invitation request
        db (Session): database session

    Returns:
        Response: response object with status code 201
        HTTPException: 401 if organization not found
        HTTPException: 401 if user is not allowed to invite to the organization
        HTTPException: 404 if user not found
        HTTPException: 400 if user is already a member of the organization
        HTTPException: 400 if user has already been invited to the organization

    """
    # current user can invite to organization
    user: User = request.state.user
    organization: Organization = await get_organization_by_user_id(
        user_id=user.id, organization_id=organization_id, db=db
    )

    current_user_role: UserOrganizationRole = await get_user_org_role(
        user, organization_id, db
    )
    if current_user_role.user_role not in [UserRole.creator, UserRole.admin]:
        raise HTTPException(
            status_code=401, detail="User is not allowed to invite to the organization"
        )

    invited_user: User | None = db.exec(
        select(User).where(User.email == invitation.email)
    ).first()
    if invited_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # check if user is already a member of the organization
    user_organization_role: UserOrganizationRole | None = db.exec(
        select(UserOrganizationRole)
        .where(UserOrganizationRole.user_id == invited_user.id)
        .where(UserOrganizationRole.organization_id == organization_id)
    ).first()

    if user_organization_role:
        raise HTTPException(
            status_code=400, detail="User is already a member of the organization"
        )
    # check if user has already been invited to the organization with the same role
    user_invitation: Invitation | None = db.exec(
        select(Invitation)
        .where(Invitation.user_id == invited_user.id)
        .where(Invitation.organization_id == organization_id)
        .where(Invitation.role == UserRole.staff)
        .where(Invitation.inviter_id == user.id)
    ).first()

    if user_invitation:
        raise HTTPException(
            status_code=400, detail="User has already been invited to the organization"
        )

    user_invitation: Invitation | None = Invitation(
        user_id=invited_user.id,
        organization_id=organization_id,
        inviter_id=user.id,
    )

    try:
        db.add(user_invitation)
        db.commit()
        db.refresh(user_invitation)
        # TODO send email to invited user with invitation link
        email_sender = EmailSender()
        email_sender.send_email_background(
            background,
            invited_user.email,
            f"You have been invited to join {organization.name} organization!",
            "invitation.html",
            organization_name=organization.name,
            invitername=user.name,
            invitation_id=user_invitation.id,
            username=invited_user.name,
            client_url=getenv("CLIENT_URL"),
        )
    except:
        db.rollback()
        raise
    return Response(status_code=201)


@router.get(
    "/",
    tags=["organizations", "invitations"],
)
async def get_organization_invitations(
    request: Request,
    organization_id: UUID,
    db: Session = Depends(get_db_session),
) -> list[OrganizationInvitationResponse]:
    """
    Get all invitations for an organization

    Args:
        request (Request): request object
        organization_id (UUID): organization id
        db (Session): database session

    Returns:
        list[OrganizationInvitationResponse]: list of organization invitations
        HTTPException: 401 if organization not found
        HTTPException: 401 if user is not allowed to see invitations
    """

    # TODO: think about invitation business logic
    #  - data will be returned
    user: User = request.state.user
    organization: Organization | None = await get_organization_by_user_id(
        user_id=user.id, organization_id=organization_id, db=db
    )
    # get user role in organization
    user_organization_role: UserOrganizationRole = await get_user_org_role(
        user, organization_id, db
    )
    if user_organization_role.user_role not in [UserRole.creator, UserRole.admin]:
        raise HTTPException(
            status_code=401, detail="User is not allowed to see invitations"
        )

    invitations: list[Invitation] = organization.invitations
    invitations_response: list[OrganizationInvitationResponse] = []
    for invitation in invitations:
        inviter: User = invitation.inviter
        invited_user: User = invitation.user
        invitation_response = OrganizationInvitationResponse(
            id=invitation.id,
            role=invitation.role,
            status=invitation.status,
            organization_id=invitation.organization_id,
            created_at=invitation.created_at,
            updated_at=invitation.updated_at,
            inviter=Inviter(
                id=inviter.id,
                name=inviter.name,
                email=inviter.email,
            ),
            user=InvitedUser(
                id=invited_user.id,
                name=invited_user.name,
                email=invited_user.email,
            ),
        )
        invitations_response.append(invitation_response)

    return invitations_response


@router.delete(
    "/{invitation_id}",
    tags=["organizations", "invitations"],
)
async def delete_organization_invitation(
    request: Request,
    organization_id: UUID,
    invitation_id: UUID,
    db: Session = Depends(get_db_session),
) -> Response:
    """
    Delete an invitation for an organization

    Args:
        request (Request): request object
        organization_id (UUID): organization id
        invitation_id (UUID): invitation id
        db (Session): database session

    Returns:

        Response: response object with status code 204
        HTTPException: 401 if organization not found
        HTTPException: 401 if user is not allowed to delete invitations
        HTTPException: 404 if invitation not found
    """

    user: User = request.state.user

    user_organization_role: UserOrganizationRole = await get_user_org_role(
        user, organization_id, db
    )
    if user_organization_role.user_role not in [UserRole.creator, UserRole.admin]:
        raise HTTPException(
            status_code=401, detail="User is not allowed to delete invitations"
        )
    invitation: Invitation | None = db.exec(
        select(Invitation).where(Invitation.id == invitation_id)
    ).first()
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    try:
        db.delete(invitation)
        db.commit()
    except:
        db.rollback()
        raise
    return Response(status_code=204)
