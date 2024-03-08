import uuid
from sqlmodel import Field
from .abstract_model import AbstractModel
from enum import Enum as PyEnum
from sqlalchemy import Enum


class UserOrganization(AbstractModel, table=True):
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="user.id")
    organization_id: uuid.UUID = Field(primary_key=True, foreign_key="organization.id")


class InvitationState(PyEnum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class Invitation(AbstractModel, table=True):
    status: InvitationState = Field(
        sa_column=Enum(InvitationState, native_enum=False, create_constraint=False)
    )
    user_id: uuid.UUID = Field(foreign_key="user.id")
    organization_id: uuid.UUID = Field(foreign_key="organization.id")
