"""
Notification schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class NotificationCreate(BaseModel):
    user_id: Optional[int] = None
    title: str = Field(..., min_length=2, max_length=150)
    message: str = Field(..., min_length=2)
    category: str = Field(default="academic")  # academic, fee, attendance, system


class NotificationResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    title: str
    message: str
    category: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
