"""
Student Repository with advanced querying, search, and filtering.
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc
from app.models.student import Student
from .base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    def __init__(self, db: Session):
        super().__init__(Student, db)

    def get_by_register_number(self, reg_num: str) -> Optional[Student]:
        cleaned = reg_num.strip().upper()
        return self.db.query(Student).filter(
            func.upper(Student.register_number) == cleaned
        ).first()

    def get_by_email(self, email: str) -> Optional[Student]:
        cleaned = email.strip().lower()
        return self.db.query(Student).filter(
            func.lower(Student.email) == cleaned
        ).first()

    def find_duplicate(
        self,
        first_name: Optional[str],
        last_name: Optional[str],
        date_of_birth: Optional[str]
    ) -> Optional[Student]:
        if not first_name or not last_name or not date_of_birth:
            return None
        return self.db.query(Student).filter(
            func.lower(Student.first_name) == first_name.strip().lower(),
            func.lower(Student.last_name) == last_name.strip().lower(),
            Student.date_of_birth == date_of_birth.strip()
        ).first()

    def search_and_filter(
        self,
        search: Optional[str] = None,
        department: Optional[str] = None,
        academic_year: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "id",
        sort_desc: bool = False
    ) -> Tuple[List[Student], int]:
        query = self.db.query(Student)

        # Search across full_name, register_number, email
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Student.full_name).like(term),
                    func.lower(Student.register_number).like(term),
                    func.lower(Student.email).like(term)
                )
            )

        if department and department.strip():
            query = query.filter(func.lower(Student.department) == department.strip().lower())

        if academic_year and academic_year.strip():
            query = query.filter(func.lower(Student.academic_year) == academic_year.strip().lower())

        if status and status.strip():
            query = query.filter(func.lower(Student.status) == status.strip().lower())

        total = query.count()

        # Sorting
        sort_col = getattr(Student, sort_by, Student.id)
        if sort_desc:
            query = query.order_by(desc(sort_col))
        else:
            query = query.order_by(asc(sort_col))

        items = query.offset(skip).limit(limit).all()
        return items, total
