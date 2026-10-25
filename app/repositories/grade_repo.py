"""
Grade repository.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.grade import GradeEntry
from app.models.examination import Examination
from .base import BaseRepository


class GradeRepository(BaseRepository[GradeEntry]):
    def __init__(self, db: Session):
        super().__init__(GradeEntry, db)

    def find_entry(self, examination_id: int, student_id: int) -> Optional[GradeEntry]:
        return self.db.query(GradeEntry).filter(
            GradeEntry.examination_id == examination_id,
            GradeEntry.student_id == student_id
        ).first()

    def get_by_student(self, student_id: int) -> List[GradeEntry]:
        return self.db.query(GradeEntry).filter(GradeEntry.student_id == student_id).all()

    def get_by_examination(self, examination_id: int) -> List[GradeEntry]:
        return self.db.query(GradeEntry).filter(GradeEntry.examination_id == examination_id).all()
