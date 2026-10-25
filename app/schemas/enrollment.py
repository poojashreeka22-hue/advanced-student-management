"""
Enrollment schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class EnrollmentBase(BaseModel):
    student_id: int
    course_id: int
    academic_year: str = Field(default="2026-2027")
    semester: int = Field(default=1, ge=1, le=8)
    status: str = Field(default="enrolled")


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentUpdate(BaseModel):
    status: Optional[str] = None  # enrolled, completed, dropped, withdrawn
    grade_point: Optional[float] = Field(None, ge=0.0, le=4.0)
    letter_grade: Optional[str] = None


class EnrollmentResponse(EnrollmentBase):
    id: int
    grade_point: Optional[float] = None
    letter_grade: Optional[str] = None
    enrolled_at: datetime
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    student_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
