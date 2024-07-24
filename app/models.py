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


@event.listens_for(AbstractModel, "before_update", propagate=True)
def before_update(mapper, connection, target):
    target.updated_at = datetime.now()


class UserRole(str, PyEnum):
    creator = "creator"
    admin = "admin"
    staff = "staff"


class UserOrganizationRole(AbstractModel, table=True):
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="user.id")
    organization_id: uuid.UUID = Field(primary_key=True, foreign_key="organization.id")
    user_role: UserRole = Field(
        sa_type=Enum(UserRole), nullable=False, default=UserRole.staff
    )
    organization: "Organization" = Relationship(
        back_populates="members_roles",
    )


class User(AbstractModel, table=True):
    name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True)
    image_url: str = Field(nullable=True)
    organizations: list["Organization"] = Relationship(
        back_populates="members",
        link_model=UserOrganizationRole,
        sa_relationship=relationship(
            "Organization",
            secondary="userorganizationrole",
            primaryjoin="User.id == UserOrganizationRole.user_id",
            secondaryjoin="Organization.id == UserOrganizationRole.organization_id",
            back_populates="members",
            overlaps="members",
            lazy="joined",
            viewonly=True,
        ),
    )
    invitations: list["Invitation"] = Relationship(
        back_populates="user",
        sa_relationship=relationship(
            foreign_keys="Invitation.user_id",
            cascade="all, delete-orphan",
        ),
    )


class InvitationStatus(str, PyEnum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class Organization(AbstractModel, table=True):
    name: str = Field(nullable=False)
    owner: uuid.UUID = Field(nullable=False, foreign_key="user.id")
    members: list["User"] = Relationship(
        back_populates="organizations",
        link_model=UserOrganizationRole,
        sa_relationship=relationship(
            "User",
            secondary="userorganizationrole",
            primaryjoin="Organization.id == UserOrganizationRole.organization_id",
            secondaryjoin="User.id == UserOrganizationRole.user_id",
            back_populates="organizations",
            lazy="joined",
            viewonly=True,
        ),
    )
    events: list["Event"] = Relationship(back_populates="organization")
    members_roles: list["UserOrganizationRole"] = Relationship(
        back_populates="organization",
        sa_relationship=relationship(
            cascade="all, delete-orphan", overlaps="members,organizations"
        ),
    )
    invitations: list["Invitation"] = Relationship(back_populates="organization")
    contact_email: str = Field(nullable=True)
    description: str = Field(nullable=True)
    logo_url: str = Field(nullable=True)
    website: str = Field(nullable=True)


class Invitation(AbstractModel, table=True):
    role: UserRole = Field(
        sa_type=Enum(UserRole), nullable=False, default=UserRole.staff
    )
    status: InvitationStatus = Field(
        sa_type=Enum(InvitationStatus), nullable=False, default=InvitationStatus.pending
    )
    user_id: uuid.UUID = Field(foreign_key="user.id")
    organization_id: uuid.UUID = Field(foreign_key="organization.id")
    inviter_id: uuid.UUID = Field(foreign_key="user.id")
    inviter: User = Relationship(
        back_populates="invitations",
        sa_relationship=relationship(foreign_keys="Invitation.inviter_id"),
    )
    user: User = Relationship(
        back_populates="invitations",
        sa_relationship=relationship(
            foreign_keys="Invitation.user_id", overlaps="invitations"
        ),
    )
    organization: Organization = Relationship(
        back_populates="invitations",
        sa_relationship=relationship(foreign_keys="Invitation.organization_id"),
    )


class EventStatus(str, PyEnum):
    SCHEDULED = "SCHEDULED"
    PENDING = "PENDING"


class Event(AbstractModel, table=True):
    name: str = Field(nullable=False)
    cover_image_url: str = Field(nullable=True)
    description: str = Field(nullable=True)
    status: EventStatus = Field(
        sa_type=Enum(EventStatus), nullable=False, default=EventStatus.PENDING
    )
    start_date: datetime = Field(nullable=False)
    end_date: datetime = Field(nullable=False)
    location: str = Field(nullable=True)
    max_tickets: int = Field(nullable=False, default=0, description="0 means unlimited")
    organization_id: uuid.UUID = Field(foreign_key="organization.id")
    tickets: list["Ticket"] = Relationship(back_populates="event")
    organization: Organization = Relationship(back_populates="events")
    attendees_logs: list["AttendeesLog"] = Relationship(back_populates="event")


class TicketStatus(str, PyEnum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class Ticket(AbstractModel, table=True):
    event_id: uuid.UUID = Field(foreign_key="event.id")
    status: TicketStatus = Enum(
        TicketStatus, nullable=False, default=TicketStatus.pending
    )
    status: TicketStatus = Field(
        sa_type=Enum(TicketStatus), nullable=False, default=TicketStatus.pending
    )
    event: Event = Relationship(back_populates="tickets")
    owner_email: str = Field(nullable=False)
    owner_name: str = Field(nullable=False)
    attendees_logs: list["AttendeesLog"] = Relationship(back_populates="ticket")


class AttendeeStatus(str, PyEnum):
    joined = "joined"
    left = "left"


class AttendeesLog(AbstractModel, table=True):
    event_id: uuid.UUID = Field(foreign_key="event.id")
    ticket_id: uuid.UUID = Field(foreign_key="ticket.id")
    status: AttendeeStatus = Field(
        sa_type=Enum(AttendeeStatus), nullable=False, default=AttendeeStatus.joined
    )
    event: Event = Relationship(back_populates="attendees_logs")
    ticket: Ticket = Relationship(back_populates="attendees_logs")
