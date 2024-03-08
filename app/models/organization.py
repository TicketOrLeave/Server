import uuid
from sqlmodel import Field, Relationship
from .abstract_model import AbstractModel
from .link_models import UserOrganization


class Organization(AbstractModel, table=True):

    name: str = Field(nullable=False)
    owner: uuid.UUID = Field(nullable=False, foreign_key="user.id")
    members: list["User"] = Relationship(
        back_populates="organizations", link_model=UserOrganization
    )
