"""
Attendance Domain Service: Marking, Session Validation, Threshold Shortage Calculations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.attendance_repo import AttendanceRepository
from app.repositories.student_repo import StudentRepository
from app.repositories.course_repo import CourseRepository
from app.models.attendance import AttendanceRecord
from app.schemas.attendance import AttendanceCreate, BulkAttendanceCreate
from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    ValidationException
)
from app.utils.calculations import calculate_attendance_percentage


class AttendanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AttendanceRepository(db)
        self.student_repo = StudentRepository(db)
        self.course_repo = CourseRepository(db)

    def record_attendance(
        self,
        data: AttendanceCreate,
        recorded_by: Optional[str] = None
    ) -> AttendanceRecord:
        valid_states = {"present", "absent", "late", "excused"}
        norm_status = data.status.strip().lower()
        if norm_status not in valid_states:
            raise ValidationException(f"Invalid attendance status '{data.status}'. Allowed: {valid_states}")

        # Check student and course exist
        if not self.student_repo.get(data.student_id):
            raise EntityNotFoundException("Student", data.student_id)
        if not self.course_repo.get(data.course_id):
            raise EntityNotFoundException("Course", data.course_id)

        # Duplicate check
        existing = self.repo.find_record(
            data.student_id, data.course_id, data.session_date, data.slot_number
        )
        if existing:
            raise DuplicateEntityException(
                "AttendanceRecord",
                "session",
                f"Student {data.student_id}, Course {data.course_id} on {data.session_date} Slot {data.slot_number}"
            )

        record = AttendanceRecord(
            student_id=data.student_id,
            course_id=data.course_id,
            session_date=data.session_date.strip(),
            slot_number=data.slot_number,
            status=norm_status,
            notes=data.notes,
            recorded_by=recorded_by,
            is_cancelled=data.is_cancelled
        )
        return self.repo.create(record)

    def record_bulk_attendance(
        self,
        bulk_data: BulkAttendanceCreate,
        recorded_by: Optional[str] = None
    ) -> List[AttendanceRecord]:
        if not self.course_repo.get(bulk_data.course_id):
            raise EntityNotFoundException("Course", bulk_data.course_id)

        results = []
        for item in bulk_data.records:
            existing = self.repo.find_record(
                item.student_id, bulk_data.course_id, bulk_data.session_date, bulk_data.slot_number
            )
            if existing:
                existing.status = item.status.strip().lower()
                existing.notes = item.notes
                existing.recorded_by = recorded_by
                self.repo.update(existing)
                results.append(existing)
            else:
                record = AttendanceRecord(
                    student_id=item.student_id,
                    course_id=bulk_data.course_id,
                    session_date=bulk_data.session_date.strip(),
                    slot_number=bulk_data.slot_number,
                    status=item.status.strip().lower(),
                    notes=item.notes,
                    recorded_by=recorded_by,
                    is_cancelled=False
                )
                results.append(self.repo.create(record))

        return results

    def get_student_course_attendance(
        self,
        student_id: int,
        course_id: int,
        min_threshold: float = 75.0
    ) -> Dict[str, Any]:
        records = self.repo.get_student_course_records(student_id, course_id)
        records_dict = [
            {"status": r.status, "is_cancelled": r.is_cancelled}
            for r in records
        ]
        calc = calculate_attendance_percentage(records_dict, min_threshold)
        return {
            "student_id": student_id,
            "course_id": course_id,
            **calc
        }

    def get_student_overall_attendance(
        self,
        student_id: int,
        min_threshold: float = 75.0
    ) -> Dict[str, Any]:
        records = self.repo.get_student_all_records(student_id)
        records_dict = [
            {"status": r.status, "is_cancelled": r.is_cancelled}
            for r in records
        ]
        calc = calculate_attendance_percentage(records_dict, min_threshold)
        return {
            "student_id": student_id,
            **calc
        }
