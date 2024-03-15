from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from app.models import User, Organization, UserRole


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
