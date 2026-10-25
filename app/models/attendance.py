"""
Attendance record model.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    session_date = Column(String(20), nullable=False, index=True)
    slot_number = Column(Integer, default=1, nullable=False)
    status = Column(String(20), default="present", nullable=False)  # present, absent, late, excused
    notes = Column(String(255), nullable=True)
    recorded_by = Column(String(100), nullable=True)
    is_cancelled = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "session_date", "slot_number", name="uq_attendance_session"),
    )

    student_rel = relationship("Student", back_populates="attendance_records")
    course_rel = relationship("Course")

    def __repr__(self) -> str:
        return f"<Attendance(student_id={self.student_id}, date='{self.session_date}', status='{self.status}')>"
