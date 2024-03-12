from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from app.models import User, Organization, UserRole


class OrganizationsResponse(BaseModel):
    organizations: list[Organization]


class OrganizationInvitationRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.staff


class Inviter(BaseModel):
    id: UUID
    name: str
    email: EmailStr


class InvitedUser(Inviter):
    pass


class InvitationResponse(BaseModel):
    id: UUID
    role: UserRole
    status: str
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    inviter: Inviter
    user: InvitedUser


class OrganizationInvitationsResponse(BaseModel):
    invitations: list[InvitationResponse]
