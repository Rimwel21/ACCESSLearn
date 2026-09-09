from datetime import datetime

from pydantic import BaseModel, Field


class PushSubscriptionKeys(BaseModel):
    p256dh: str = Field(min_length=1)
    auth: str = Field(min_length=1)


class PushSubscriptionIn(BaseModel):
    endpoint: str = Field(min_length=1)
    keys: PushSubscriptionKeys


class PushSubscriptionOut(BaseModel):
    id: int
    endpoint: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PushConfigOut(BaseModel):
    enabled: bool
    public_key: str | None = None
