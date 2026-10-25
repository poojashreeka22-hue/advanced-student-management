"""
Course and Curriculum API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.academic_service import AcademicService
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course_in: CourseCreate, db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.create_course(course_in)


@router.get("", response_model=List[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.get_all_courses()


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.get_course(course_id)


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, course_in: CourseUpdate, db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.update_course(course_id, course_in)
