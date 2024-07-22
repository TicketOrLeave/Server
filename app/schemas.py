from typing import Literal
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from app.models import EventStatus, User, Organization, UserRole, InvitationStatus


class OrganizationsResponse(BaseModel):
    organizations: list[Organization]


class OrganizationInvitationRequest(BaseModel):
    email: EmailStr


class Inviter(BaseModel):
    id: UUID
    name: str
    email: EmailStr


class InvitedUser(Inviter):
    pass


class OrganizationInvitationResponse(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    inviter: Inviter
    user: InvitedUser


class UserInvitationOrganization(BaseModel):
    id: UUID
    name: str


class UserInvitation(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    inviter: Inviter
    organization: UserInvitationOrganization


class InvitationStatusRequest(BaseModel):
    status: Literal[InvitationStatus.accepted, InvitationStatus.rejected] = Field(...)


class UserChangeRoleRequest(BaseModel):
    role: Literal[UserRole.admin, UserRole.staff]


class OrganizationRequestBody(BaseModel):
    name: str
    contact_email: EmailStr
    description: str = None
    logo_url: str = None
    website: str = None

    class Config:
        extra = "forbid"


class ReservationEventResponse(BaseModel):
    id: UUID
    name: str
    start_date: datetime
    end_date: datetime
    location: str | None
    description: str | None
    cover_image_url: str | None


class TicketRequest(BaseModel):
    name: str
    email: str

    class Config:
        extra = "forbid"


class EventResponse(BaseModel):
    id: UUID
    name: str
    status: EventStatus
    start_date: datetime
    end_date: datetime
    location: str | None
    description: str | None
    cover_image_url: str | None
    max_tickets: int
    created_at: datetime
    updated_at: datetime


class EventResponseWithOrganization(EventResponse):
    organization_name: str


class OrganizationMember(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    image_url: str
    role: UserRole


class EventRequest(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    max_tickets: int = 0
    organization_id: UUID
    description: str = None
    location: str = None
    cover_image_url: str = None

    class Config:
        extra = "forbid"


class DeleteEventRequestSchema(BaseModel):
    organization_id: UUID

    class Config:
        extra = "forbid"


class TicketRequest(BaseModel):
    name: str
    email: str

    class Config:
        extra = "forbid"


class EditEventRequest(EventRequest):
    status: EventStatus

    class Config:
        extra = "forbid"
