"""
Examination Configuration API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.grade_service import GradeService
from app.schemas.examination import ExaminationCreate, ExaminationResponse
from app.models.course import Course

router = APIRouter(prefix="/examinations", tags=["Examinations"])


@router.post("", response_model=ExaminationResponse, status_code=status.HTTP_201_CREATED)
def create_examination(data: ExaminationCreate, db: Session = Depends(get_db)):
    service = GradeService(db)
    exam = service.create_examination(data)
    course = db.query(Course).filter(Course.id == exam.course_id).first()
    return ExaminationResponse(
        id=exam.id,
        course_id=exam.course_id,
        title=exam.title,
        exam_type=exam.exam_type,
        exam_date=exam.exam_date,
        max_marks=exam.max_marks,
        weightage_percent=exam.weightage_percent,
        academic_year=exam.academic_year,
        semester=exam.semester,
        created_at=exam.created_at,
        course_code=course.code if course else None
    )


@router.get("/course/{course_id}", response_model=List[ExaminationResponse])
def get_course_examinations(course_id: int, db: Session = Depends(get_db)):
    service = GradeService(db)
    exams = service.get_course_examinations(course_id)
    course = db.query(Course).filter(Course.id == course_id).first()
    return [
        ExaminationResponse(
            id=e.id,
            course_id=e.course_id,
            title=e.title,
            exam_type=e.exam_type,
            exam_date=e.exam_date,
            max_marks=e.max_marks,
            weightage_percent=e.weightage_percent,
            academic_year=e.academic_year,
            semester=e.semester,
            created_at=e.created_at,
            course_code=course.code if course else None
        )
        for e in exams
    ]
