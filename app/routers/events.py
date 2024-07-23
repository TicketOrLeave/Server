import select
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Response
from app.models import (
    EventStatus,
    User,
    Event,
    UserOrganizationRole,
    UserRole,
)
from app.database import get_db_session
from starlette.requests import Request
from sqlmodel import Session, select
from fastapi import APIRouter

from app.schemas import (
    EventRequest,
    EditEventRequest,
    EventResponse,
    EventResponseWithOrganization,
)

router = APIRouter()


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


@router.post("/", tags=["events"], response_model=Event)
async def create_event(
    request: Request,
    event: EventRequest,
    organization_id: UUID,
    db: Session = Depends(get_db_session),
) -> Event | None:
    user: User = request.state.user
    """
    create event for organization

    Args:
        request (Request): request object
        event (EventRequest): event request object
        db (Session, optional): database session. Defaults to Depends(get_db_session).
    
    Returns:
        Event : created event
        HTTPException: 401 if user is not the owner of the organization
        HTTPException: 400 if start date is greater than end date
    
    """
    # check if user in organization
    user_org_role: UserOrganizationRole = await get_user_org_role(
        user, organization_id, db
    )
    if user_org_role.user_role not in [UserRole.creator, UserRole.admin]:
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
        organization_id=organization_id,
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
        raise HTTPException(status_code=500, detail="Error creating event")
    return event


@router.put("/{event_id}", tags=["events"])
async def update_event(
    request: Request,
    organization_id: UUID,
    event_id: UUID,
    event_request: EditEventRequest,
    db: Session = Depends(get_db_session),
) -> Event | None:
    """
    update event for organization

    Args:
        request (Request): request object
        event_id (UUID): event id
        event_request (EditEventRequest): event request object
        db (Session, optional): database session. Defaults to Depends(get_db_session).
    Returns:
         Event: updated event
         HTTPException: 404 if event not found
         HTTPException: 500 if error updating event

    """
    user: User = request.state.user
    user_org_role: UserOrganizationRole = await get_user_org_role(
        user, organization_id, db
    )

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
        .where(Event.organization_id == organization_id)
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


@router.get(
    "/{event_id}", tags=["events"], response_model=EventResponseWithOrganization
)
async def get_event_by_id_with_organization_name(
    request: Request, event_id: UUID, db: Session = Depends(get_db_session)
) -> EventResponseWithOrganization:
    """
    get event by id with organization name

    Args:
        request (Request): request object
        event_id (UUID): event id
        db (Session, optional): database session. Defaults to Depends(get_db_session).

    Returns:
        EventResponseWithOrganization: event response with organization name
        HTTPException: 404 if event not found
    """
    event: Event | None = db.exec(select(Event).where(Event.id == event_id)).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventResponseWithOrganization(
        id=event.id,
        name=event.name,
        status=event.status,
        start_date=event.start_date,
        end_date=event.end_date,
        location=event.location,
        description=event.description,
        cover_image_url=event.cover_image_url,
        max_tickets=event.max_tickets,
        created_at=event.created_at,
        updated_at=event.updated_at,
        organization_name=event.organization.name,
    )


@router.delete("/{event_id}", tags=["events"])
async def delete_event(
    request: Request,
    event_id: UUID,
    organization_id: UUID,
    db: Session = Depends(get_db_session),
) -> Response:
    """
    delete event for organization

    Args:
        request (Request): request object
        event_id (UUID): event id
        organization_id (UUID): organization id
        db (Session, optional): database session.

    Returns:
        Response: response object with status code 204
        HTTPException: 404 if event not found
        HTTPException: 500 if error deleting event

    """
    user: User = request.state.user
    user_org_role: UserOrganizationRole = await get_user_org_role(
        user, organization_id, db
    )
    if user_org_role.user_role not in [UserRole.creator, UserRole.admin]:
        raise HTTPException(
            status_code=401, detail="User is not the owner of the organization"
        )
    event: Event | None = db.exec(
        select(Event)
        .where(Event.id == event_id)
        .where(Event.organization_id == organization_id)
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


@router.get(
    "/",
    tags=["events", "organizations"],
    response_model=list[EventResponse],
)
async def get_events(
    request: Request, organization_id: UUID, db: Session = Depends(get_db_session)
) -> list[EventResponse]:
    """
    args:
        organization_id: UUID
        request: Request
        db: Session = Depends(get_db_session)
    return:
        list of events
    description:
        Get all events of an organization
    """
    user: User = request.state.user

    # check if user in organization
    await get_user_org_role(user, organization_id, db)
    events: list[Event] = db.exec(
        select(Event).where(Event.organization_id == organization_id)
    ).all()

    return events
