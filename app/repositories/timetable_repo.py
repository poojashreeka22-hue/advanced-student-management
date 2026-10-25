"""
Timetable and Classroom repository.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.timetable import Classroom, TimetableSlot
from app.utils.calculations import times_overlap


class TimetableRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_classroom(self, classroom_id: int) -> Optional[Classroom]:
        return self.db.query(Classroom).filter(Classroom.id == classroom_id).first()

    def get_all_classrooms(self) -> List[Classroom]:
        return self.db.query(Classroom).all()

    def create_classroom(self, room: Classroom) -> Classroom:
        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)
        return room

    def get_all_slots(
        self,
        academic_year: Optional[str] = None,
        semester: Optional[int] = None
    ) -> List[TimetableSlot]:
        q = self.db.query(TimetableSlot)
        if academic_year:
            q = q.filter(TimetableSlot.academic_year == academic_year)
        if semester:
            q = q.filter(TimetableSlot.semester == semester)
        return q.all()

    def create_slot(self, slot: TimetableSlot) -> TimetableSlot:
        self.db.add(slot)
        self.db.commit()
        self.db.refresh(slot)
        return slot

    def check_conflicts(
        self,
        classroom_id: int,
        faculty_id: int,
        day_of_week: str,
        start_time: str,
        end_time: str,
        academic_year: str,
        semester: int,
        exclude_slot_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Check if classroom or faculty is already booked for overlapping time.
        """
        day_slots = self.db.query(TimetableSlot).filter(
            TimetableSlot.day_of_week == day_of_week,
            TimetableSlot.academic_year == academic_year,
            TimetableSlot.semester == semester
        ).all()

        for slot in day_slots:
            if exclude_slot_id and slot.id == exclude_slot_id:
                continue

            if times_overlap(start_time, end_time, slot.start_time, slot.end_time):
                if slot.classroom_id == classroom_id:
                    return f"Classroom {classroom_id} is already occupied on {day_of_week} ({slot.start_time} - {slot.end_time})"
                if slot.faculty_id == faculty_id:
                    return f"Faculty member {faculty_id} is already teaching on {day_of_week} ({slot.start_time} - {slot.end_time})"

        return None
