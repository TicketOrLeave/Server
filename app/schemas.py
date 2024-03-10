from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models import User, Organization


class OrganizationsResponse(BaseModel):
    organizations: list[Organization]
