"""
Attendance schemas.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AttendanceBase(BaseModel):
    student_id: int
    course_id: int
    session_date: str = Field(..., description="YYYY-MM-DD")
    slot_number: int = Field(default=1, ge=1, le=8)
    status: str = Field(default="present")  # present, absent, late, excused
    notes: Optional[str] = None
    is_cancelled: bool = False


class AttendanceCreate(AttendanceBase):
    pass


class BulkAttendanceItem(BaseModel):
    student_id: int
    status: str = Field(default="present")
    notes: Optional[str] = None


class BulkAttendanceCreate(BaseModel):
    course_id: int
    session_date: str
    slot_number: int = 1
    records: List[BulkAttendanceItem]


class AttendanceResponse(AttendanceBase):
    id: int
    recorded_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StudentAttendanceSummary(BaseModel):
    student_id: int
    course_id: int
    total_sessions: int
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    attendance_percentage: float
    is_shortage: bool
