from typing import Optional
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

router = APIRouter()
router.include_router(events_router, prefix="/{organization_id}/events")
router.include_router(invitations_router, prefix="/{organization_id}/invitations")


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
) -> list[OrganizationMember]:
    user: User = request.state.user

    organization: Optional[Organization] = next(
        (org for org in user.organizations if org.id == organization_id), None
    )
    if organization is None:
        # unauthorized
        raise HTTPException(status_code=401, detail="Organization not found")

    # get all members of the organization with roles
    members = db.exec(
        select(User, UserOrganizationRole)
        .join(UserOrganizationRole)
        .where(UserOrganizationRole.organization_id == organization_id)
    ).all()

    print(list(members))

    members_with_roles = []
    for member, role in members:
        members_with_roles.append(
            OrganizationMember(
                id=member.id,
                name=member.name,
                email=member.email,
                image_url=member.image_url,
                role=role.user_role,
            )
        )
    return members_with_roles


@router.post("/", tags=["organizations"], response_model=Organization)
async def create_organization(
    request: Request,
    request_body: OrganizationRequestBody,
    db: Session = Depends(get_db_session),
) -> Organization | Response:
    user: User = request.state.user
    try:
        db.begin()
        organization = Organization(owner=user.id, **request_body.model_dump())
        db.add(organization)
        db.commit()
        user_organization = UserOrganizationRole(
            user_id=user.id, organization_id=organization.id, user_role=UserRole.creator
        )
        db.add(user_organization)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Organization not created")
    db.refresh(organization)
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
    user: User = request.state.user
    organization: Optional[Organization] = next(
        (org for org in user.organizations if org.id == organization_id), None
    )
    if organization is None:
        raise HTTPException(status_code=401, detail="Organization not found")

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
    organization: Optional[Organization] = next(
        (org for org in user.organizations if org.id == organization_id), None
    )
    # TODO: check if user is the owner of the organization
    if organization is None:
        raise HTTPException(status_code=401, detail="Organization not found")

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
            status_code=401, detail="User is not authorized to remove members"
        )
    elif target_user_organization_role.user_role == UserRole.creator:
        raise HTTPException(
            status_code=401, detail="Cannot remove the creator from the organization"
        )
    elif (
        current_user_organization_role.user_role == UserRole.admin
        and target_user_organization_role.user_role == UserRole.admin
    ):
        raise HTTPException(status_code=401, detail="Admin cannot remove another admin")

    try:
        db.delete(target_user_organization_role)
        db.commit()
    except:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="User not removed from the organization"
        )

    return Response(status_code=204)
