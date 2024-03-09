from sqlmodel import SQLModel
from datetime import datetime
from sqlalchemy import event
from enum import Enum as PyEnum
from sqlalchemy import Enum
import uuid
from sqlmodel import Field, Relationship


class AbstractModel(SQLModel):
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)


class TenantModel(AbstractModel):
    tenant_id: str = Field(nullable=True)


@event.listens_for(AbstractModel, "before_update", propagate=True)
def before_update(mapper, connection, target):
    target.updated_at = datetime.now()


class UserOrganization(TenantModel, table=True):
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="user.id")
    organization_id: uuid.UUID = Field(primary_key=True, foreign_key="organization.id")


class User(TenantModel, table=True):
    name: str = Field(nullable=False)
    email: str = Field(nullable=False)
    image_url: str = Field(nullable=True)
    organizations: list["Organization"] = Relationship(
        back_populates="members", link_model=UserOrganization
    )


class InvitationState(PyEnum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class Invitation(TenantModel, table=True):
    status: InvitationState = Field(
        sa_column=Enum(InvitationState, native_enum=False, create_constraint=False)
    )
    user_id: uuid.UUID = Field(foreign_key="user.id")
    organization_id: uuid.UUID = Field(foreign_key="organization.id")


class Organization(AbstractModel, table=True):
    name: str = Field(nullable=False)
    owner: uuid.UUID = Field(nullable=False, foreign_key="user.id")
    members: list["User"] = Relationship(
        back_populates="organizations", link_model=UserOrganization
    )
