"""
Grade entry and GPA calculation schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class GradeEntryBase(BaseModel):
    examination_id: int
    student_id: int
    marks_obtained: float = Field(..., ge=0.0)
    is_absent: bool = False
    letter_grade: Optional[str] = None
    remarks: Optional[str] = None


class GradeEntryCreate(GradeEntryBase):
    pass


class GradeEntryUpdate(BaseModel):
    marks_obtained: Optional[float] = Field(None, ge=0.0)
    is_absent: Optional[bool] = None
    letter_grade: Optional[str] = None
    remarks: Optional[str] = None
    amendment_reason: Optional[str] = Field(None, description="Required for modifying an existing grade")


class GradeEntryResponse(GradeEntryBase):
    id: int
    graded_by: Optional[str] = None
    amendment_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    student_name: Optional[str] = None
    student_register_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AcademicTranscriptItem(BaseModel):
    course_code: str
    course_title: str
    credits: int
    marks_percentage: float
    letter_grade: str
    grade_point: float


class AcademicTranscript(BaseModel):
    student_id: int
    student_name: str
    register_number: str
    department: str
    academic_year: str
    semester: int
    items: List[AcademicTranscriptItem]
    total_credits: int
    gpa: float
