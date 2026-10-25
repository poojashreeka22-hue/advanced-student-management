"""
Grade entry model.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base


class GradeEntry(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    examination_id = Column(Integer, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    marks_obtained = Column(Float, nullable=False)
    is_absent = Column(Boolean, default=False, nullable=False)
    letter_grade = Column(String(5), nullable=True)
    remarks = Column(String(255), nullable=True)
    graded_by = Column(String(100), nullable=True)
    amendment_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("examination_id", "student_id", name="uq_exam_student_grade"),
    )

    examination_rel = relationship("Examination", back_populates="grades")
    student_rel = relationship("Student", back_populates="grades")

    def __repr__(self) -> str:
        return f"<GradeEntry(exam_id={self.examination_id}, student_id={self.student_id}, marks={self.marks_obtained})>"
