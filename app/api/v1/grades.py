"""
Grade Entry, Amendment, and Academic Transcript API Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.grade_service import GradeService
from app.schemas.grade import (
    GradeEntryCreate,
    GradeEntryUpdate,
    GradeEntryResponse,
    AcademicTranscript
)
from app.api.dependencies import get_current_user_optional
from app.models.user import User
from app.models.student import Student

router = APIRouter(prefix="/grades", tags=["Grades"])


@router.post("", response_model=GradeEntryResponse, status_code=status.HTTP_201_CREATED)
def enter_grade(
    data: GradeEntryCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    service = GradeService(db)
    graded_by = current_user.username if current_user else "faculty"
    grade = service.enter_grade(data, graded_by=graded_by)
    student = db.query(Student).filter(Student.id == grade.student_id).first()
    return GradeEntryResponse(
        id=grade.id,
        examination_id=grade.examination_id,
        student_id=grade.student_id,
        marks_obtained=grade.marks_obtained,
        is_absent=grade.is_absent,
        letter_grade=grade.letter_grade,
        remarks=grade.remarks,
        graded_by=grade.graded_by,
        amendment_reason=grade.amendment_reason,
        created_at=grade.created_at,
        updated_at=grade.updated_at,
        student_name=student.full_name if student else None,
        student_register_number=student.register_number if student else None
    )


@router.patch("/{grade_id}", response_model=GradeEntryResponse)
def amend_grade(
    grade_id: int,
    data: GradeEntryUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    service = GradeService(db)
    amended_by = current_user.username if current_user else "faculty"
    grade = service.amend_grade(grade_id, data, amended_by=amended_by)
    student = db.query(Student).filter(Student.id == grade.student_id).first()
    return GradeEntryResponse(
        id=grade.id,
        examination_id=grade.examination_id,
        student_id=grade.student_id,
        marks_obtained=grade.marks_obtained,
        is_absent=grade.is_absent,
        letter_grade=grade.letter_grade,
        remarks=grade.remarks,
        graded_by=grade.graded_by,
        amendment_reason=grade.amendment_reason,
        created_at=grade.created_at,
        updated_at=grade.updated_at,
        student_name=student.full_name if student else None,
        student_register_number=student.register_number if student else None
    )


@router.get("/student/{student_id}/transcript", response_model=AcademicTranscript)
def get_transcript(student_id: int, db: Session = Depends(get_db)):
    service = GradeService(db)
    return service.generate_student_transcript(student_id)
