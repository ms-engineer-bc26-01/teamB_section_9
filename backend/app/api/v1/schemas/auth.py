import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str | None
    default_region_code: str | None
    subscription_status: Literal["free", "active", "canceled"]
    stripe_customer_id: str | None
    created_at: datetime


class UpdateDefaultRegionRequest(BaseModel):
    region_code: str
