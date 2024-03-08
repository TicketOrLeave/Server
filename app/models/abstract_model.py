from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import event
import uuid


class AbstractModel(SQLModel):
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)


class TenantModel(AbstractModel):
    tenant_id: str = Field(nullable=False)


@event.listens_for(AbstractModel, "before_update", propagate=True)
def before_update(mapper, connection, target):
    target.updated_at = datetime.now()
