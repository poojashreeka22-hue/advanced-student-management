"""
Student course enrollment model.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year = Column(String(20), nullable=False)
    semester = Column(Integer, nullable=False)
    status = Column(String(20), default="enrolled", nullable=False)  # enrolled, completed, dropped, withdrawn
    grade_point = Column(Float, nullable=True)
    letter_grade = Column(String(5), nullable=True)
    enrolled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "academic_year", "semester", name="uq_student_course_year_sem"),
    )

    student_rel = relationship("Student", back_populates="enrollments")
    course_rel = relationship("Course", back_populates="enrollments")

    def __repr__(self) -> str:
        return f"<Enrollment(student_id={self.student_id}, course_id={self.course_id}, status='{self.status}')>"
