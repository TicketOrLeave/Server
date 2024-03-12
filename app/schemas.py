from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from app.models import User, Organization, UserRole


class OrganizationsResponse(BaseModel):
    organizations: list[Organization]


class OrganizationInvitationRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.staff
