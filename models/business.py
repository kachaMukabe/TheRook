from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class Business(BaseModel):
    Id: Optional[str] = Field(None)
    name: str
    owner_id: str
    business_id: str
    phone_number: str
    rapid_pro_channel: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    subscription_plan: str
