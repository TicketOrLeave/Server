from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import event


class AbstractModel(SQLModel):
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)


@event.listens_for(AbstractModel, "before_update", propagate=True)
def before_update(mapper, connection, target):
    target.updated_at = datetime.now()
