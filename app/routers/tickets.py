import select
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Response,Query
from app.models import (
    EventStatus,
    Organization,
    User,
    Event,
    UserOrganizationRole,
    UserRole, Ticket, TicketStatus,
)
from app.database import get_db_session
from starlette.requests import Request
from sqlmodel import Session, select
from fastapi import APIRouter

from app.schemas import TicketRequest

router = APIRouter()



@router.post("/", tags=["tickets"], response_model=Ticket)
async def create_ticket(
        request: Request,
        ticket: TicketRequest,
        event_id: UUID = Query(None),
        db: Session = Depends(get_db_session)
) -> Event | None:

    if event_id is None:
        raise HTTPException(status_code=400, detail="Event ID is required")

    # first check if event exists
    event: Event = db.exec(select(Event).where(Event.id == event_id)).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")


    # count number of tickets for event
    tickets_count = db.exec(select(Ticket).where(Ticket.event_id == event_id)).all().__len__()
    if tickets_count >= event.max_tickets:
        raise HTTPException(status_code=400, detail="Event tickets sold out")

    ticket: Ticket = Ticket(
        owner_name=ticket.name,
        owner_email=ticket.email,
        event_id=event_id,
        status=TicketStatus.pending,
    )

    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
    except:
        db.rollback()
        raise
    return ticket


@router.get("/{ticket_id}", tags=["tickets"], response_model=Ticket)
async def get_ticket(
        request: Request,
        ticket_id: UUID,
        db: Session = Depends(get_db_session)
) -> Ticket | None:
    ticket: Ticket = db.exec(select(Ticket).where(Ticket.id == ticket_id)).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get('/', tags=["tickets"], response_model=List[Ticket])
async def get_tickets(
        request: Request,
        event_id: UUID,
        db: Session = Depends(get_db_session)
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
        raise HTTPException(status_code=401, detail="User is not the owner of the organization")
    tickets: List[Ticket] = db.exec(select(Ticket).where(Ticket.event_id == event_id)).all()
    return tickets
