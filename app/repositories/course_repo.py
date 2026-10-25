"""
Course repository.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.course import Course
from .base import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, db: Session):
        super().__init__(Course, db)

    def get_by_code(self, code: str) -> Optional[Course]:
        return self.db.query(Course).filter(
            func.upper(Course.code) == code.strip().upper()
        ).first()

    def get_by_department(self, department_id: int) -> List[Course]:
        return self.db.query(Course).filter(
            Course.department_id == department_id,
            Course.is_active.is_(True)
        ).all()
