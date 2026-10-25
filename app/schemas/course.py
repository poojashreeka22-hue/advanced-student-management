"""
Course schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CourseBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=30)
    title: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    credits: int = Field(default=3, ge=1, le=10)
    department_id: int
    prerequisite_id: Optional[int] = None
    max_capacity: int = Field(default=60, ge=1, le=500)
    semester: int = Field(default=1, ge=1, le=8)
    academic_year: str = Field(default="2026-2027")
    is_active: bool = True


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    credits: Optional[int] = Field(None, ge=1, le=10)
    department_id: Optional[int] = None
    prerequisite_id: Optional[int] = None
    max_capacity: Optional[int] = Field(None, ge=1, le=500)
    semester: Optional[int] = Field(None, ge=1, le=8)
    academic_year: Optional[str] = None
    is_active: Optional[bool] = None


class CourseResponse(CourseBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
