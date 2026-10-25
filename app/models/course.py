"""
Course and curriculum model.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    credits = Column(Integer, default=3, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    prerequisite_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    max_capacity = Column(Integer, default=60, nullable=False)
    semester = Column(Integer, default=1, nullable=False)
    academic_year = Column(String(20), default="2026-2027", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    department_rel = relationship("Department", back_populates="courses")
    prerequisite = relationship("Course", remote_side=[id])
    enrollments = relationship("Enrollment", back_populates="course_rel", cascade="all, delete-orphan")
    examinations = relationship("Examination", back_populates="course_rel", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Course(code='{self.code}', title='{self.title}', credits={self.credits})>"
