import select
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from app.models import Event, UserOrganizationRole, UserRole, Ticket
from app.database import get_db_session
from starlette.requests import Request
from sqlmodel import Session, select
from fastapi import APIRouter


router = APIRouter()


@router.get("/", tags=["tickets"], response_model=List[Ticket])
async def get_tickets(
    request: Request, event_id: UUID, db: Session = Depends(get_db_session)
) -> List[Ticket]:
    user = request.state.user
    event: Event = db.exec(select(Event).where(Event.id == event_id)).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    user_org_role: UserOrganizationRole = db.exec(
        select(UserOrganizationRole).where(
            UserOrganizationRole.user_id == user.id,
            UserOrganizationRole.organization_id == event.organization_id,
        )
    ).first()
    if not user_org_role:
        raise HTTPException(status_code=404, detail="Organization not found")
    if user_org_role.user_role not in [UserRole.creator, UserRole.admin]:
        raise HTTPException(
            status_code=401, detail="User is not the owner of the organization"
        )
    tickets: List[Ticket] = db.exec(
        select(Ticket).where(Ticket.event_id == event_id)
    ).all()
    return tickets
