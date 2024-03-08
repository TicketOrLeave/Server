from .abstract_model import AbstractModel
from .link_models import UserOrganization
from sqlmodel import Field, Relationship


class User(AbstractModel, table=True):
    name: str = Field(nullable=False)
    email: str = Field(nullable=False)
    image_url: str = Field(nullable=True)
    organizations: list["Organization"] = Relationship(
        back_populates="members", link_model=UserOrganization
    )
