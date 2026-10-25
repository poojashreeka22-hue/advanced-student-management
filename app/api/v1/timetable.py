"""
Classroom and Timetable Scheduling API Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.timetable_service import TimetableService
from app.schemas.timetable import (
    ClassroomCreate,
    ClassroomResponse,
    TimetableSlotCreate,
    TimetableSlotResponse
)
from app.models.course import Course
from app.models.faculty import Faculty
from app.models.timetable import Classroom

router = APIRouter(prefix="/timetable", tags=["Timetable"])


@router.post("/classrooms", response_model=ClassroomResponse, status_code=status.HTTP_201_CREATED)
def create_classroom(data: ClassroomCreate, db: Session = Depends(get_db)):
    service = TimetableService(db)
    return service.create_classroom(data)


@router.get("/classrooms", response_model=List[ClassroomResponse])
def get_classrooms(db: Session = Depends(get_db)):
    service = TimetableService(db)
    return service.get_all_classrooms()


@router.post("/slots", response_model=TimetableSlotResponse, status_code=status.HTTP_201_CREATED)
def create_slot(data: TimetableSlotCreate, db: Session = Depends(get_db)):
    service = TimetableService(db)
    slot = service.create_slot(data)
    course = db.query(Course).filter(Course.id == slot.course_id).first()
    faculty = db.query(Faculty).filter(Faculty.id == slot.faculty_id).first()
    room = db.query(Classroom).filter(Classroom.id == slot.classroom_id).first()
    return TimetableSlotResponse(
        id=slot.id,
        course_id=slot.course_id,
        faculty_id=slot.faculty_id,
        classroom_id=slot.classroom_id,
        day_of_week=slot.day_of_week,
        start_time=slot.start_time,
        end_time=slot.end_time,
        academic_year=slot.academic_year,
        semester=slot.semester,
        course_code=course.code if course else None,
        course_title=course.title if course else None,
        faculty_name=faculty.full_name if faculty else None,
        room_number=room.room_number if room else None
    )


@router.get("/slots", response_model=List[TimetableSlotResponse])
def get_slots(
    academic_year: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    service = TimetableService(db)
    slots = service.get_timetable(academic_year, semester)
    res = []
    for slot in slots:
        course = db.query(Course).filter(Course.id == slot.course_id).first()
        faculty = db.query(Faculty).filter(Faculty.id == slot.faculty_id).first()
        room = db.query(Classroom).filter(Classroom.id == slot.classroom_id).first()
        res.append(TimetableSlotResponse(
            id=slot.id,
            course_id=slot.course_id,
            faculty_id=slot.faculty_id,
            classroom_id=slot.classroom_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            academic_year=slot.academic_year,
            semester=slot.semester,
            course_code=course.code if course else None,
            course_title=course.title if course else None,
            faculty_name=faculty.full_name if faculty else None,
            room_number=room.room_number if room else None
        ))
    return res
