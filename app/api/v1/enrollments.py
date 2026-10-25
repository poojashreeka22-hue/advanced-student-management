"""
Course Enrollment API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.enrollment_service import EnrollmentService
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse
from app.models.course import Course
from app.models.student import Student

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post("", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_student(data: EnrollmentCreate, db: Session = Depends(get_db)):
    service = EnrollmentService(db)
    enr = service.enroll_student(data)
    # Enrich response
    course = db.query(Course).filter(Course.id == enr.course_id).first()
    student = db.query(Student).filter(Student.id == enr.student_id).first()
    return EnrollmentResponse(
        id=enr.id,
        student_id=enr.student_id,
        course_id=enr.course_id,
        academic_year=enr.academic_year,
        semester=enr.semester,
        status=enr.status,
        grade_point=enr.grade_point,
        letter_grade=enr.letter_grade,
        enrolled_at=enr.enrolled_at,
        course_code=course.code if course else None,
        course_title=course.title if course else None,
        student_name=student.full_name if student else None
    )


@router.get("/student/{student_id}", response_model=List[EnrollmentResponse])
def get_student_enrollments(student_id: int, db: Session = Depends(get_db)):
    service = EnrollmentService(db)
    items = service.get_student_enrollments(student_id)
    res = []
    for enr in items:
        course = db.query(Course).filter(Course.id == enr.course_id).first()
        student = db.query(Student).filter(Student.id == enr.student_id).first()
        res.append(EnrollmentResponse(
            id=enr.id,
            student_id=enr.student_id,
            course_id=enr.course_id,
            academic_year=enr.academic_year,
            semester=enr.semester,
            status=enr.status,
            grade_point=enr.grade_point,
            letter_grade=enr.letter_grade,
            enrolled_at=enr.enrolled_at,
            course_code=course.code if course else None,
            course_title=course.title if course else None,
            student_name=student.full_name if student else None
        ))
    return res


@router.patch("/{enrollment_id}", response_model=EnrollmentResponse)
def update_enrollment(enrollment_id: int, data: EnrollmentUpdate, db: Session = Depends(get_db)):
    service = EnrollmentService(db)
    enr = service.update_enrollment(enrollment_id, data)
    course = db.query(Course).filter(Course.id == enr.course_id).first()
    student = db.query(Student).filter(Student.id == enr.student_id).first()
    return EnrollmentResponse(
        id=enr.id,
        student_id=enr.student_id,
        course_id=enr.course_id,
        academic_year=enr.academic_year,
        semester=enr.semester,
        status=enr.status,
        grade_point=enr.grade_point,
        letter_grade=enr.letter_grade,
        enrolled_at=enr.enrolled_at,
        course_code=course.code if course else None,
        course_title=course.title if course else None,
        student_name=student.full_name if student else None
    )
