import select
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Response
from app.models import Event, UserOrganizationRole, UserRole, Ticket
from app.database import get_db_session
from starlette.requests import Request
from sqlmodel import Session, select
from fastapi import APIRouter
from sqlalchemy.orm import joinedload
from datetime import datetime

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


@router.delete("/{ticket_id}", tags=["tickets"])
async def delete_ticket(
    request: Request, ticket_id: UUID, db: Session = Depends(get_db_session)
):
    user = request.state.user
    ticket: Ticket = db.exec(select(Ticket).where(
        Ticket.id == ticket_id)).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    event: Event = db.exec(select(Event).where(
        Event.id == ticket.event_id)).first()
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
    db.delete(ticket)
    db.commit()
    return Response(status_code=204)


@router.get("/{ticket_id}", tags=["tickets"], response_model=Ticket)
async def get_ticket(
    request: Request,
    ticket_id: UUID,
    event_id: UUID,
    db: Session = Depends(get_db_session),
) -> Ticket:
    user = request.state.user
    ticket: Ticket = db.exec(
        select(Ticket)
        .options(joinedload(Ticket.event))
        .where(Ticket.id == ticket_id)
        .where(Ticket.event_id == event_id)
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    user_org_role: UserOrganizationRole = db.exec(
        select(UserOrganizationRole).where(
            UserOrganizationRole.user_id == user.id,
            UserOrganizationRole.organization_id == ticket.event.organization_id,
        )
    ).first()

    if not user_org_role:
        # User is not part of the organization
        raise HTTPException(
            status_code=403, detail="User not authorized to view ticket"
        )
    if ticket.event.end_date < datetime.now():
        # Event has ended
        raise HTTPException(status_code=403, detail="Event has ended")
    return ticket
