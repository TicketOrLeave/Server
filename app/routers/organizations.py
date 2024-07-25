from fastapi import APIRouter, Body, HTTPException, Response, Depends
from app.models import (
    User,
    Organization,
    UserOrganizationRole,
    UserRole,
)
from app.database import get_db_session
from starlette.requests import Request
from app.routers.events import router as events_router
from app.routers.invitations import router as invitations_router
from app.schemas import (
    OrganizationsResponse,
    OrganizationRequestBody,
    OrganizationMember,
    UserChangeRoleRequest,
)
from uuid import UUID
from sqlmodel import Session, select

from app.utilities.database import get_organization_by_user_id, get_user_org_role

router = APIRouter()
router.include_router(events_router, prefix="/{organization_id}/events")
router.include_router(invitations_router, prefix="/{organization_id}/invitations")


@router.get("/", tags=["organizations"], response_model=list[Organization])
async def get_user_organizations(
    request: Request,
) -> OrganizationsResponse:
    """
    Returns a list of organizations that the user is a part of.

    Args:
        request (Request): The request object.

    Returns:
        OrganizationsResponse: A list of organizations that the user is a part of.
    """

    user: User = request.state.user
    return user.organizations


@router.get(
    "/{organization_id}",
    tags=["organizations"],
    response_model=Organization,
)
async def get_organization(
    request: Request, organization_id: UUID, db: Session = Depends(get_db_session)
) -> Organization:
    """
    get organization by id

    Args:
        request (Request): The request object.
        organization_id (UUID): The organization id.
        db (Session): The database session.

    Returns:
        Organization: The organization object
    """
    user: User = request.state.user
    organization = await get_organization_by_user_id(user.id, organization_id, db)
    return organization


@router.get("/{organization_id}/members", tags=["organizations", "members"])
async def get_organization_members(
    request: Request, organization_id: UUID, db: Session = Depends(get_db_session)
) -> list[OrganizationMember]:
    """
    get organization members by organization id

    Args:
        request (Request): The request object.
        organization_id (UUID): The organization id.
        db (Session): The database session.

    Returns:
        list[OrganizationMember]: A list of organization members with their roles.
    """

    user: User = request.state.user

    await get_organization_by_user_id(user.id, organization_id, db)

    users_with_role = db.exec(
        select(
            User.id,
            User.name,
            User.email,
            User.image_url,
            UserOrganizationRole.user_role,
        )
        .join(UserOrganizationRole)
        .where(UserOrganizationRole.organization_id == organization_id)
    ).all()

    members_with_roles = []
    for user_id, name, email, image_url, role in users_with_role:
        members_with_roles.append(
            OrganizationMember(
                id=user_id,
                name=name,
                email=email,
                image_url=image_url,
                role=role,
            )
        )

    return members_with_roles


@router.post("/", tags=["organizations"], response_model=Organization)
async def create_organization(
    request: Request,
    request_body: OrganizationRequestBody,
    db: Session = Depends(get_db_session),
) -> Organization:
    """
    create organization

    Args:
        request (Request): The request object.
        request_body (OrganizationRequestBody): The request body.
        db (Session): The database session.

    Returns:
        Organization: The organization object or a response object.
        HTTPException (status_code=400): If the organization is not created.

    """
    user: User = request.state.user
    try:
        organization = Organization(owner=user.id, **request_body.model_dump())
        user_organization = UserOrganizationRole(
            user_id=user.id,
            organization_id=organization.id,
            user_role=UserRole.creator,
        )
        db.add_all([organization, user_organization])
        db.commit()
        db.refresh(organization)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Organization not created")

    return organization


@router.delete("/{organization_id}", tags=["organizations"])
async def delete_organization(request: Request, organization_id: UUID) -> Response:
    user: User = request.state.user
    db = request.state.db
    organization: Organization = await get_organization_by_user_id(
        user.id, organization_id, db
    )
    """
    delete organization

    Args:
        request (Request): The request object.
        organization_id (UUID): The organization id.

    Returns:
        Response: A response object.
        HTTPException (status_code=401): If the user is not the owner of the organization.
    """

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


@router.put(
    "/{organization_id}/members/{user_id}",
    tags=["organizations", "members"],
)
async def change_user_role(
    request: Request,
    organization_id: UUID,
    user_id: UUID,
    role: UserChangeRoleRequest = Body(...),
    db: Session = Depends(get_db_session),
) -> Response:
    """
    change user role in the organization

    Args:
        request (Request): The request object.
        organization_id (UUID): The organization id.
        user_id (UUID): The user id.
        role (UserChangeRoleRequest): The role request.
        db (Session): The database session.

    Returns:
        Response: A response object.
        HTTPException (status_code=401): If the user is not authorized to change roles.
        HTTPException (status_code=401): If the user is not found in the organization.
        HTTPException (status_code=401): If the user is the owner of the organization.
        HTTPException (status_code=401): If the user is not authorized to change roles to admin.
        HTTPException (status_code=401): If the user is already in the same role.
        HTTPException (status_code=401): If the user is not authorized to change roles.
        HTTPException (status_code=401): If the user is not authorized to remove members.
        HTTPException (status_code=401): If the user is not authorized to remove the creator from the organization.
        HTTPException (status_code=401): If the user is not authorized to remove another admin.
        HTTPException (status_code=400): If the role is not updated.

    """
    user: User = request.state.user
    await get_organization_by_user_id(user.id, organization_id, db)

    if user.id == user_id:
        raise HTTPException(status_code=401, detail="User cannot change their own role")

    target_user_organization_role = db.exec(
        select(UserOrganizationRole)
        .where(UserOrganizationRole.user_id == user_id)
        .where(UserOrganizationRole.organization_id == organization_id)
    ).first()
    if target_user_organization_role is None:
        raise HTTPException(
            status_code=401, detail="User not found in the organization"
        )
    current_user_organization_role = db.exec(
        select(UserOrganizationRole)
        .where(UserOrganizationRole.user_id == user.id)
        .where(UserOrganizationRole.organization_id == organization_id)
    ).first()
    if current_user_organization_role.user_role == UserRole.staff:
        raise HTTPException(
            status_code=401, detail="User is not authorized to change roles"
        )
    elif (
        current_user_organization_role.user_role == UserRole.admin
        and role == UserRole.admin
    ):
        raise HTTPException(
            status_code=401, detail="User is not authorized to change roles to admin"
        )

    elif target_user_organization_role.user_role == UserRole.creator:
        raise HTTPException(status_code=401, detail="Cannot change role of the creator")
    elif target_user_organization_role.user_role == role:
        raise HTTPException(status_code=401, detail="User is already in the same role")
    target_user_organization_role.user_role = role.role
    try:
        db.add(target_user_organization_role)
        db.commit()
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="Role not updated")

    return Response(status_code=204)


@router.delete(
    "/{organization_id}/members/{user_id}",
    tags=["organizations", "members"],
)
async def remove_user_from_organization(
    request: Request,
    organization_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db_session),
) -> Response:
    user: User = request.state.user
    organization = await get_organization_by_user_id(user.id, organization_id, db)

    # TODO: check if user is the owner of the organization
    # only the owner of the organization can remove members

    target_user_organization_role: UserOrganizationRole = await get_user_org_role(
        user_id, organization_id, db
    )

    if organization.owner != user.id:
        raise HTTPException(
            status_code=401, detail="User is not the owner of the organization"
        )

    if organization.owner == user_id:
        raise HTTPException(
            status_code=401, detail="Cannot remove the owner from the organization"
        )

    try:
        db.delete(target_user_organization_role)
        db.commit()
    except:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="User not removed from the organization"
        )

    return Response(status_code=204)
