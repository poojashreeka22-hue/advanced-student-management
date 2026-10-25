"""
Attendance repository.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.attendance import AttendanceRecord
from .base import BaseRepository


class AttendanceRepository(BaseRepository[AttendanceRecord]):
    def __init__(self, db: Session):
        super().__init__(AttendanceRecord, db)

    def find_record(
        self,
        student_id: int,
        course_id: int,
        session_date: str,
        slot_number: int
    ) -> Optional[AttendanceRecord]:
        return self.db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.course_id == course_id,
            AttendanceRecord.session_date == session_date,
            AttendanceRecord.slot_number == slot_number
        ).first()

    def get_student_course_records(self, student_id: int, course_id: int) -> List[AttendanceRecord]:
        return self.db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.course_id == course_id
        ).all()

    def get_student_all_records(self, student_id: int) -> List[AttendanceRecord]:
        return self.db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student_id
        ).all()

    def get_course_session_records(
        self,
        course_id: int,
        session_date: str,
        slot_number: int
    ) -> List[AttendanceRecord]:
        return self.db.query(AttendanceRecord).filter(
            AttendanceRecord.course_id == course_id,
            AttendanceRecord.session_date == session_date,
            AttendanceRecord.slot_number == slot_number
        ).all()
