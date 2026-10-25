"""
Faculty Member API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.academic_service import AcademicService
from app.schemas.faculty import FacultyCreate, FacultyUpdate, FacultyResponse

router = APIRouter(prefix="/faculty", tags=["Faculty"])


@router.post("", response_model=FacultyResponse, status_code=status.HTTP_201_CREATED)
def create_faculty(faculty_in: FacultyCreate, db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.create_faculty(faculty_in)


@router.get("", response_model=List[FacultyResponse])
def get_all_faculty(db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.get_all_faculty()


@router.get("/{faculty_id}", response_model=FacultyResponse)
def get_faculty(faculty_id: int, db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.get_faculty(faculty_id)


@router.put("/{faculty_id}", response_model=FacultyResponse)
def update_faculty(faculty_id: int, faculty_in: FacultyUpdate, db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.update_faculty(faculty_id, faculty_in)
