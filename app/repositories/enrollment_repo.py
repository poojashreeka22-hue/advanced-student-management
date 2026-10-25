"""
Enrollment repository.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.enrollment import Enrollment
from .base import BaseRepository


class EnrollmentRepository(BaseRepository[Enrollment]):
    def __init__(self, db: Session):
        super().__init__(Enrollment, db)

    def find_enrollment(
        self,
        student_id: int,
        course_id: int,
        academic_year: str,
        semester: int
    ) -> Optional[Enrollment]:
        return self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
            Enrollment.academic_year == academic_year,
            Enrollment.semester == semester
        ).first()

    def get_by_student(self, student_id: int) -> List[Enrollment]:
        return self.db.query(Enrollment).filter(Enrollment.student_id == student_id).all()

    def get_by_course(self, course_id: int, academic_year: str, semester: int) -> List[Enrollment]:
        return self.db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
            Enrollment.academic_year == academic_year,
            Enrollment.semester == semester,
            Enrollment.status == "enrolled"
        ).all()

    def count_enrolled(self, course_id: int, academic_year: str, semester: int) -> int:
        return self.db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
            Enrollment.academic_year == academic_year,
            Enrollment.semester == semester,
            Enrollment.status == "enrolled"
        ).count()
