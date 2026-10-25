"""
Timetable and Classroom schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ClassroomBase(BaseModel):
    room_number: str = Field(..., min_length=1, max_length=50)
    building: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(default=60, ge=10, le=500)
    room_type: str = Field(default="lecture_hall")


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomResponse(ClassroomBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TimetableSlotBase(BaseModel):
    course_id: int
    faculty_id: int
    classroom_id: int
    day_of_week: str = Field(..., description="Monday..Saturday")
    start_time: str = Field(..., description="HH:MM (e.g. 09:00)")
    end_time: str = Field(..., description="HH:MM (e.g. 10:30)")
    academic_year: str = Field(default="2026-2027")
    semester: int = Field(default=1, ge=1, le=8)


class TimetableSlotCreate(TimetableSlotBase):
    pass


class TimetableSlotResponse(TimetableSlotBase):
    id: int
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    faculty_name: Optional[str] = None
    room_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConflictCheckResult(BaseModel):
    has_conflict: bool
    conflict_type: Optional[str] = None  # classroom, faculty, student
    message: Optional[str] = None
