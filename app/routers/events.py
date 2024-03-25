import select
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Response
from app.models import (
    EventStatus,
    Organization,
    User,
    Event,
    UserOrganizationRole,
    UserRole,
)
from app.database import get_db_session
from starlette.requests import Request
from sqlmodel import Session, select
from fastapi import APIRouter

from app.schemas import EventRequest, EventResponse, EditEventRequest

router = APIRouter()


@router.get("/", tags=["events"], response_model=list[EventResponse])
async def organization_events(
    request: Request, org_id: str, db: Session = Depends(get_db_session)
) -> list[EventResponse]:
    user: User = request.state.user

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


@router.post("/", tags=["events"], response_model=Event)
async def create_event(
    request: Request, event: EventRequest, db: Session = Depends(get_db_session)
) -> Event | None:
    user: User = request.state.user

    # check if user in organization
    user_org_role: UserOrganizationRole = db.exec(
        select(UserOrganizationRole).where(
            UserOrganizationRole.user_id == user.id,
            UserOrganizationRole.organization_id == event.orgId,
        )
    ).first()
    # TODO check if user is owner of organization
    if user_org_role is None:
        # unauthorized
        raise HTTPException(status_code=404, detail="Organization not found")
    elif user_org_role.user_role not in [UserRole.creator, UserRole.admin]:
        # unauthorized
        raise HTTPException(
            status_code=401, detail="User is not the owner of the organization"
        )
    elif event.start_date > event.end_date:
        raise HTTPException(
            status_code=400, detail="Start date cannot be greater than end date"
        )

    event: Event = Event(
        name=event.name,
        organization_id=event.orgId,
        cover_image_url=event.cover_image_url,
        description=event.description,
        location=event.location,
        start_date=event.start_date,
        end_date=event.end_date,
        max_tickets=event.max_tickets,
        status=EventStatus.PENDING,
    )

    try:
        db.add(event)
        db.commit()
        db.refresh(event)
    except:
        db.rollback()
        raise
    return event


@router.delete("/{event_id}", tags=["events"])
async def delete_event(
    request: Request,
    event_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db_session),
) -> Response:
    user: User = request.state.user
    user_org_role: UserOrganizationRole = db.exec(
        select(UserOrganizationRole).where(
            UserOrganizationRole.user_id == user.id,
            UserOrganizationRole.organization_id == org_id,
        )
    ).first()

    if user_org_role is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if user_org_role.user_role not in [UserRole.creator, UserRole.admin]:
        raise HTTPException(
            status_code=401, detail="User is not the owner of the organization"
        )
    event: Event | None = db.exec(
        select(Event).where(Event.id == event_id).where(Event.organization_id == org_id)
    ).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    try:
        db.delete(event)
        db.commit()
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting event")
    return Response(status_code=204)


@router.put("/{event_id}", tags=["events"])
async def update_event(
    request: Request,
    event_id: UUID,
    event_request: EditEventRequest,
    db: Session = Depends(get_db_session),
) -> Event | None:
    user: User = request.state.user
    user_org_role: UserOrganizationRole = db.exec(
        select(UserOrganizationRole).where(
            UserOrganizationRole.user_id == user.id,
            UserOrganizationRole.organization_id == event_request.orgId,
        )
    ).first()

    if user_org_role is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if user_org_role.user_role not in [UserRole.creator, UserRole.admin]:
        raise HTTPException(
            status_code=401, detail="User is not the owner of the organization"
        )
    if event_request.start_date > event_request.end_date:
        raise HTTPException(
            status_code=400, detail="Start date cannot be greater than end date"
        )
    event: Event | None = db.exec(
        select(Event)
        .where(Event.id == event_id)
        .where(Event.organization_id == event_request.orgId)
    ).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    event.name = event_request.name
    event.cover_image_url = event_request.cover_image_url
    event.description = event_request.description
    event.location = event_request.location
    event.start_date = event_request.start_date
    event.end_date = event_request.end_date
    event.max_tickets = event_request.max_tickets
    event.status = event_request.status
    try:
        db.add(event)
        db.commit()
        db.refresh(event)
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error updating event")
    return event
