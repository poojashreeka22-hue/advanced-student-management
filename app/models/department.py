"""
Department model.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), unique=True, nullable=False)
    head_of_department = Column(String(100), nullable=True)
    hod_faculty_id = Column(Integer, ForeignKey("faculty.id", use_alter=True, name="fk_department_hod_faculty_id"), nullable=True)
    building = Column(String(100), nullable=True)
    budget = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    courses = relationship("Course", back_populates="department_rel", cascade="all, delete-orphan")
    faculty_members = relationship("Faculty", back_populates="department_rel", foreign_keys="[Faculty.department_id]")
    hod_faculty = relationship("Faculty", foreign_keys=[hod_faculty_id], post_update=True)

    def __repr__(self) -> str:
        return f"<Department(code='{self.code}', name='{self.name}')>"
