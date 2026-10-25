"""
Faculty schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FacultyBase(BaseModel):
    employee_id: str = Field(..., min_length=2, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    department_id: int
    designation: str = Field(default="Assistant Professor", max_length=50)
    specialization: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class FacultyCreate(FacultyBase):
    pass


class FacultyUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    phone_number: Optional[str] = None
    department_id: Optional[int] = None
    designation: Optional[str] = None
    specialization: Optional[str] = None
    is_active: Optional[bool] = None


class FacultyResponse(FacultyBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
