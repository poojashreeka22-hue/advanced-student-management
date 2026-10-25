"""
Examination schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ExaminationBase(BaseModel):
    course_id: int
    title: str = Field(..., min_length=2, max_length=100)
    exam_type: str = Field(default="midterm")  # quiz, midterm, final, assignment, practical
    exam_date: Optional[str] = None
    max_marks: float = Field(default=100.0, gt=0.0)
    weightage_percent: float = Field(default=30.0, gt=0.0, le=100.0)
    academic_year: str = Field(default="2026-2027")
    semester: int = Field(default=1, ge=1, le=8)


class ExaminationCreate(ExaminationBase):
    pass


class ExaminationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=100)
    exam_type: Optional[str] = None
    exam_date: Optional[str] = None
    max_marks: Optional[float] = Field(None, gt=0.0)
    weightage_percent: Optional[float] = Field(None, gt=0.0, le=100.0)


class ExaminationResponse(ExaminationBase):
    id: int
    created_at: datetime
    course_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
