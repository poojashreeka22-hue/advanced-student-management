"""
Timetable and Scheduling Service with Conflict Detection.
Enforces real classroom, faculty existence/active status, and time conflict safeguards.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.timetable_repo import TimetableRepository
from app.repositories.course_repo import CourseRepository
from app.models.timetable import Classroom, TimetableSlot
from app.models.faculty import Faculty
from app.schemas.timetable import (
    ClassroomCreate,
    TimetableSlotCreate,
    ConflictCheckResult
)
from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    ScheduleConflictException,
    ValidationException
)


class TimetableService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TimetableRepository(db)
        self.course_repo = CourseRepository(db)

    def create_classroom(self, data: ClassroomCreate) -> Classroom:
        existing = self.db.query(Classroom).filter(Classroom.room_number == data.room_number.strip()).first()
        if existing:
            raise DuplicateEntityException("Classroom", "room_number", data.room_number)

        room = Classroom(
            room_number=data.room_number.strip(),
            building=data.building.strip(),
            capacity=data.capacity,
            room_type=data.room_type
        )
        return self.repo.create_classroom(room)

    def get_all_classrooms(self) -> List[Classroom]:
        return self.repo.get_all_classrooms()

    def create_slot(self, data: TimetableSlotCreate) -> TimetableSlot:
        # Check course exists and is active
        course = self.course_repo.get(data.course_id)
        if not course:
            raise EntityNotFoundException("Course", data.course_id)
        if not course.is_active:
            raise ValidationException(f"Cannot schedule timetable slot for inactive course '{course.code}'.")

        # Check classroom exists
        classroom = self.repo.get_classroom(data.classroom_id)
        if not classroom:
            raise EntityNotFoundException("Classroom", data.classroom_id)

        # Check faculty exists and is active
        faculty = self.db.query(Faculty).filter(Faculty.id == data.faculty_id).first()
        if not faculty:
            raise EntityNotFoundException("Faculty", data.faculty_id)
        if not faculty.is_active:
            raise ValidationException(f"Cannot schedule slot for inactive faculty member '{faculty.full_name}'.")

        # Time range validation
        if data.start_time >= data.end_time:
            raise ValidationException(f"Start time ({data.start_time}) must be earlier than end time ({data.end_time}).")

        # Check time conflicts for classroom and faculty
        conflict = self.repo.check_conflicts(
            classroom_id=data.classroom_id,
            faculty_id=data.faculty_id,
            day_of_week=data.day_of_week,
            start_time=data.start_time,
            end_time=data.end_time,
            academic_year=data.academic_year,
            semester=data.semester
        )
        if conflict:
            raise ScheduleConflictException(conflict)

        slot = TimetableSlot(
            course_id=data.course_id,
            faculty_id=data.faculty_id,
            classroom_id=data.classroom_id,
            day_of_week=data.day_of_week,
            start_time=data.start_time,
            end_time=data.end_time,
            academic_year=data.academic_year,
            semester=data.semester
        )
        return self.repo.create_slot(slot)

    def get_timetable(
        self,
        academic_year: Optional[str] = None,
        semester: Optional[int] = None
    ) -> List[TimetableSlot]:
        return self.repo.get_all_slots(academic_year, semester)
