from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    action: str
    entity_type: str
    entity_id: int | None = None
    description: str | None = None


class AuditLogCreate(AuditLogBase):
    user_id: int | None = None


class AuditLogResponse(AuditLogBase):
    id: int
    user_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )