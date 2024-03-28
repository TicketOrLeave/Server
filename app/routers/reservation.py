from datetime import datetime
import select
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Response
from app.models import (
    EventStatus,
    Event,
    Ticket,
    TicketStatus,
)
from app.schemas import ReservationEventResponse, TicketRequest
from app.database import get_db_session
from starlette.requests import Request
from sqlmodel import Session, select
from fastapi import APIRouter
from app.utilities.mail import EmailSender
import segno

router = APIRouter()


@router.get("/{event_id}", tags=["events"], response_model=ReservationEventResponse)
async def get_event(
    request: Request,
    event_id: UUID,
    db: Session = Depends(get_db_session),
) -> Event | None:
    event: Event = db.exec(
        select(Event)
        .where(Event.id == event_id)
        .where(Event.status == EventStatus.SCHEDULED)
        .where(Event.start_date > datetime.now())
    ).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return event


@router.post("/{event_id}", tags=["events"], response_model=Ticket)
async def book_ticket(
    request: Request,
    event_id: UUID,
    ticket_request: TicketRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
) -> Event | None:
    event: Event = db.exec(
        select(Event)
        .where(Event.id == event_id)
        .where(Event.status == EventStatus.SCHEDULED)
        .where(Event.start_date > datetime.now())
    ).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    tickets_count: int = (
        db.exec(select(Ticket).where(Ticket.event_id == event_id)).all().__len__()
    )
    if tickets_count >= event.max_tickets and event.max_tickets != 0:
        raise HTTPException(status_code=400, detail="No more tickets available")

    alrady_booked = db.exec(
        select(Ticket)
        .where(Ticket.event_id == event_id)
        .where(Ticket.owner_email == ticket_request.email)
    ).first()
    if alrady_booked:
        raise HTTPException(status_code=400, detail="Already booked")

    try:
        ticket = Ticket(
            event_id=event_id,
            owner_email=ticket_request.email,
            owner_name=ticket_request.name,
            status=TicketStatus.accepted,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        qr: segno.QRCode = segno.make(f"{ticket.id}")
        qr.save(f"qrcodes/{ticket.id}.png", scale=7.5)
        path = f"qrcodes/{ticket.id}.png"

        email_sinder = EmailSender()
        email_sinder.send_email_background(
            background_tasks=background_tasks,
            email=ticket.owner_email,
            subject="Ticket Confirmation",
            template_name="ticket.html",
            attachments=[path],
            name=ticket.owner_name,
            event_name=event.name,
            location=event.location == None and "Online" or event.location,
            date=event.start_date.strftime("%Y-%m-%d"),
        )

    except:
        db.rollback()
        raise

    return ticket
