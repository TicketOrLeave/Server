import select
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Response
from app.models import (
    EventRequest,
    EventResponse,
    EventStatus,
    Organization,
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


@router.post("/", tags=["events"], response_model=Event)
async def create_event(
    request: Request, event: EventRequest, db: Session = Depends(get_db_session)
) -> Event | None:
    user: User = request.state.user
    try:
        db.begin()
        event: Event = Event(
            name=event.name,
            organization_id=event.orgId,
            cover_image_url=event.cover_image_url,
            description=event.description,
            location=event.location,
            start_date=event.start_date,
            end_date=event.end_date,
            max_tickets=event.max_tickets,
            status=EventStatus.SCHEDULED,
        )
        db.add(event)
        db.commit()
    except:
        db.rollback()
        raise
    return event


@router.delete("/{event_id}", tags=["events"])
async def delete_event(
    request: Request, event_id: UUID, org_id: UUID, db: Session = Depends(get_db_session)
) -> Response:
    user: User = request.state.user
    organization: Optional[Organization] = next(
        (org for org in user.organizations if org.id == org_id), None
    )
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if organization.owner != user.id:
        raise HTTPException(
            status_code=401, detail="User is not the owner of the organization"
        )
    if not any(event.id == event_id for event in organization.events):
        raise HTTPException(status_code=404, detail="Event not found")
    db.begin()
    event: Event = db.get(Event, event_id)
    db.delete(event)
    db.commit()
    return Response(status_code=204)