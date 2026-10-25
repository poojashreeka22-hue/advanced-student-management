"""
Attendance Marking and Verification API Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.attendance_service import AttendanceService
from app.schemas.attendance import (
    AttendanceCreate,
    BulkAttendanceCreate,
    AttendanceResponse,
    StudentAttendanceSummary
)
from app.api.dependencies import get_current_user_optional
from app.models.user import User

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def record_attendance(
    data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    service = AttendanceService(db)
    recorded_by = current_user.username if current_user else "faculty"
    return service.record_attendance(data, recorded_by=recorded_by)


@router.post("/bulk", response_model=List[AttendanceResponse], status_code=status.HTTP_201_CREATED)
def record_bulk_attendance(
    data: BulkAttendanceCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    service = AttendanceService(db)
    recorded_by = current_user.username if current_user else "faculty"
    return service.record_bulk_attendance(data, recorded_by=recorded_by)


@router.get("/student/{student_id}", response_model=StudentAttendanceSummary)
def get_student_overall_attendance(student_id: int, db: Session = Depends(get_db)):
    service = AttendanceService(db)
    calc = service.get_student_overall_attendance(student_id)
    return StudentAttendanceSummary(
        student_id=student_id,
        course_id=0,
        total_sessions=calc["total_sessions"],
        present_count=calc["present_count"],
        absent_count=calc["absent_count"],
        late_count=calc["late_count"],
        excused_count=calc["excused_count"],
        attendance_percentage=calc["attendance_percentage"],
        is_shortage=calc["is_shortage"]
    )


@router.get("/student/{student_id}/course/{course_id}", response_model=StudentAttendanceSummary)
def get_student_course_attendance(student_id: int, course_id: int, db: Session = Depends(get_db)):
    service = AttendanceService(db)
    calc = service.get_student_course_attendance(student_id, course_id)
    return StudentAttendanceSummary(
        student_id=student_id,
        course_id=course_id,
        total_sessions=calc["total_sessions"],
        present_count=calc["present_count"],
        absent_count=calc["absent_count"],
        late_count=calc["late_count"],
        excused_count=calc["excused_count"],
        attendance_percentage=calc["attendance_percentage"],
        is_shortage=calc["is_shortage"]
    )
