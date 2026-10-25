"""
Student domain model.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    register_number = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    full_name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    date_of_birth = Column(String(20), nullable=True)
    gender = Column(String(20), nullable=True)
    department = Column(String(100), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    academic_year = Column(String(50), nullable=False, index=True)
    semester = Column(Integer, default=1, nullable=False)
    status = Column(String(30), default="active", nullable=False, index=True)
    admission_date = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    guardian_name = Column(String(100), nullable=True)
    guardian_phone = Column(String(20), nullable=True)
    gpa = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    enrollments = relationship("Enrollment", back_populates="student_rel", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="student_rel", cascade="all, delete-orphan")
    grades = relationship("GradeEntry", back_populates="student_rel", cascade="all, delete-orphan")
    invoices = relationship("FeeInvoice", back_populates="student_rel", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, reg='{self.register_number}', name='{self.full_name}', status='{self.status}')>"
