import select
from fastapi import APIRouter, HTTPException, Depends
from app.models import (
    EventResponse,
    User,
    Event,
    UserOrganizationRole,
)
from app.database import get_db_session
from starlette.requests import Request
from sqlmodel import Session, select
from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["events"], response_model=list[EventResponse])
async def organization_events(
    request: Request, org_id: str, db: Session = Depends(get_db_session)
) -> list[EventResponse]:
    user: User = request.state.user

    db.begin()
    # check if user in organization
    user_org_role: UserOrganizationRole = db.exec(
        select(UserOrganizationRole).where(
            UserOrganizationRole.user_id == user.id,
            UserOrganizationRole.organization_id == org_id,
        )
    ).first()
    if user_org_role is None:
        # unauthorized
        raise HTTPException(status_code=404, detail="Organization not found")
    events: list[Event] = db.exec(
        select(Event).where(Event.organization_id == org_id)
    ).all()

    return events
