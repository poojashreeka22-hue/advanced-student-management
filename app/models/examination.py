"""
Examination model.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base


class Examination(Base):
    __tablename__ = "examinations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    exam_type = Column(String(30), default="midterm", nullable=False)  # quiz, midterm, final, assignment, practical
    exam_date = Column(String(20), nullable=True)
    max_marks = Column(Float, default=100.0, nullable=False)
    weightage_percent = Column(Float, default=30.0, nullable=False)
    academic_year = Column(String(20), default="2026-2027", nullable=False)
    semester = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    course_rel = relationship("Course", back_populates="examinations")
    grades = relationship("GradeEntry", back_populates="examination_rel", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Examination(id={self.id}, title='{self.title}', course_id={self.course_id})>"
