"""
Classroom and Timetable models.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_number = Column(String(50), unique=True, nullable=False, index=True)
    building = Column(String(100), nullable=False)
    capacity = Column(Integer, default=60, nullable=False)
    room_type = Column(String(50), default="lecture_hall", nullable=False)  # lecture_hall, lab, seminar

    slots = relationship("TimetableSlot", back_populates="classroom_rel")

    def __repr__(self) -> str:
        return f"<Classroom(room='{self.room_number}', cap={self.capacity})>"


class TimetableSlot(Base):
    __tablename__ = "timetable_slots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(String(20), nullable=False, index=True)  # Monday, Tuesday, ...
    start_time = Column(String(10), nullable=False)  # HH:MM
    end_time = Column(String(10), nullable=False)    # HH:MM
    academic_year = Column(String(20), default="2026-2027", nullable=False)
    semester = Column(Integer, default=1, nullable=False)

    course_rel = relationship("Course")
    faculty_rel = relationship("Faculty")
    classroom_rel = relationship("Classroom", back_populates="slots")

    def __repr__(self) -> str:
        return f"<TimetableSlot(day='{self.day_of_week}', time='{self.start_time}-{self.end_time}', room={self.classroom_id})>"
