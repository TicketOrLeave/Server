import select
from uuid import UUID
from fastapi import HTTPException
from app.models import (
    User,
    UserOrganizationRole,
)
from app.database import get_db_session
from sqlmodel import Session, select


async def get_user_org_role(
    user: User, organization_id: UUID, db: Session
) -> UserOrganizationRole:
    """
    get user organization role

    Args:
        user (User): user object
        organization_id (UUID): organization id
        db (Session): database session

    Returns:
        UserOrganizationRole: user organization role
        HTTPException: 404 if organization not found
    """
    user_org_role: UserOrganizationRole | None = db.exec(
        select(UserOrganizationRole).where(
            UserOrganizationRole.user_id == user.id,
            UserOrganizationRole.organization_id == organization_id,
        )
    ).first()
    if user_org_role is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return user_org_role