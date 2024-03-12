import uuid
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, Enum, SQLModel
from enum import Enum as PyEnum


class AbstractModel(SQLModel):
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)


class TenantModel(AbstractModel):
    tenant_id: str = Field(nullable=True)


@event.listens_for(AbstractModel, "before_update", propagate=True)
def before_update(mapper, connection, target):
    target.updated_at = datetime.now()


class UserRole(PyEnum):
    creator = "creator"
    admin = "admin"
    staff = "staff"


class UserOrganizationRole(TenantModel, table=True):
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="user.id")
    organization_id: uuid.UUID = Field(primary_key=True, foreign_key="organization.id")
    user_role: UserRole = Enum(UserRole, nullable=False, default=UserRole.staff)
    organization: "Organization" = Relationship(
        back_populates="members_roles",
    )


class User(TenantModel, table=True):
    name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True)
    image_url: str = Field(nullable=True)
    organizations: list["Organization"] = Relationship(
        back_populates="members", link_model=UserOrganizationRole
    )


class InvitationStatus(PyEnum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class Organization(AbstractModel, table=True):
    name: str = Field(nullable=False)
    owner: uuid.UUID = Field(nullable=False, foreign_key="user.id")
    members: list["User"] = Relationship(
        back_populates="organizations", link_model=UserOrganizationRole
    )
    events: list["Event"] = Relationship(back_populates="organization")
    members_roles: list["UserOrganizationRole"] = Relationship(
        back_populates="organization",
        sa_relationship=relationship(cascade="all, delete-orphan"),
    )


class Invitation(TenantModel, table=True):
    role: UserRole = Enum(UserRole, nullable=False, default=UserRole.staff)
    status: InvitationStatus = Enum(
        InvitationStatus, nullable=False, default=InvitationStatus.pending
    )
    user_id: uuid.UUID = Field(foreign_key="user.id")
    organization_id: uuid.UUID = Field(foreign_key="organization.id")
    inviter_id: uuid.UUID = Field(foreign_key="user.id")


class EventStatus(PyEnum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class Event(TenantModel, table=True):
    title: str = Field(nullable=False)
    cover_image_url: str = Field(nullable=True)
    description: str = Field(nullable=False)
    status: EventStatus = Enum(EventStatus, nullable=False, default=EventStatus.pending)
    start_date: datetime = Field(nullable=False)
    end_date: datetime = Field(nullable=False)
    location: str = Field(nullable=False)
    max_tickets: int = Field(nullable=False, default=0, description="0 means unlimited")
    organization_id: uuid.UUID = Field(foreign_key="organization.id")
    tickets: list["Ticket"] = Relationship(back_populates="event")
    organization: Organization = Relationship(back_populates="events")
    attendees_logs: list["AttendeesLog"] = Relationship(back_populates="event")


class TicketStatus(PyEnum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class Ticket(TenantModel, table=True):
    event_id: uuid.UUID = Field(foreign_key="event.id")
    status: TicketStatus = Enum(
        TicketStatus, nullable=False, default=TicketStatus.pending
    )
    event: Event = Relationship(back_populates="tickets")
    owner_email: str = Field(nullable=False)
    owner_name: str = Field(nullable=False)
    attendees_logs: list["AttendeesLog"] = Relationship(back_populates="ticket")


class AttendeeStatus(PyEnum):
    joined = "joined"
    left = "left"


class AttendeesLog(TenantModel, table=True):
    event_id: uuid.UUID = Field(foreign_key="event.id")
    ticket_id: uuid.UUID = Field(foreign_key="ticket.id")
    status: AttendeeStatus = Enum(AttendeeStatus, nullable=False)
    event: Event = Relationship(back_populates="attendees_logs")
    ticket: Ticket = Relationship(back_populates="attendees_logs")
