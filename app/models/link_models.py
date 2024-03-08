import uuid
from sqlmodel import Field
from .abstract_model import AbstractModel


class UserOrganization(AbstractModel, table=True):
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="user.id")
    organization_id: uuid.UUID = Field(primary_key=True, foreign_key="organization.id")
