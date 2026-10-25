"""
Enrollment Domain Service: Capacity Checks, Prerequisite Validation, Course Registrations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.enrollment_repo import EnrollmentRepository
from app.repositories.course_repo import CourseRepository
from app.repositories.student_repo import StudentRepository
from app.models.enrollment import Enrollment
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate
from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    PrerequisiteNotMetException,
    CapacityExceededException,
    ValidationException
)


class EnrollmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EnrollmentRepository(db)
        self.course_repo = CourseRepository(db)
        self.student_repo = StudentRepository(db)

    def enroll_student(self, data: EnrollmentCreate) -> Enrollment:
        # Check student exists and is active
        student = self.student_repo.get(data.student_id)
        if not student:
            raise EntityNotFoundException("Student", data.student_id)
        if student.status != "active":
            raise ValidationException(f"Cannot enroll student with status '{student.status}'. Student must be active.")

        # Check course exists and is active
        course = self.course_repo.get(data.course_id)
        if not course:
            raise EntityNotFoundException("Course", data.course_id)
        if not course.is_active:
            raise ValidationException("Cannot enroll in an inactive course.")

        # Check duplicate enrollment in same semester & year
        existing = self.repo.find_enrollment(data.student_id, data.course_id, data.academic_year, data.semester)
        if existing and existing.status in ("enrolled", "completed"):
            raise DuplicateEntityException("Enrollment", "student_course", f"{student.register_number}:{course.code}")

        # Check if student is already actively enrolled in this course in any academic period
        active_anywhere = self.db.query(Enrollment).filter(
            Enrollment.student_id == data.student_id,
            Enrollment.course_id == data.course_id,
            Enrollment.status == "enrolled"
        ).first()
        if active_anywhere:
            raise DuplicateEntityException(
                "Enrollment",
                "student_course",
                f"Student {student.register_number} is already actively enrolled in course {course.code} ({active_anywhere.academic_year} Sem {active_anywhere.semester})"
            )

        # Check if student already completed and passed this course
        completed_passed = self.db.query(Enrollment).filter(
            Enrollment.student_id == data.student_id,
            Enrollment.course_id == data.course_id,
            Enrollment.status == "completed"
        ).first()
        if completed_passed and (completed_passed.grade_point is None or completed_passed.grade_point >= 2.0):
            raise ValidationException(
                f"Student {student.register_number} has already completed and passed course '{course.code}'. Retaking passed courses is prohibited."
            )

        # Check course capacity
        current_enrolled_count = self.repo.count_enrolled(data.course_id, data.academic_year, data.semester)
        if current_enrolled_count >= course.max_capacity:
            raise CapacityExceededException(course.code, course.max_capacity)

        # Check prerequisites
        if course.prerequisite_id:
            prereq = self.course_repo.get(course.prerequisite_id)
            prereq_code = prereq.code if prereq else f"Course #{course.prerequisite_id}"

            # Check if student completed prerequisite with passing grade
            student_enrollments = self.repo.get_by_student(data.student_id)
            prereq_met = False
            for enr in student_enrollments:
                if enr.course_id == course.prerequisite_id:
                    if enr.status == "completed" and (enr.grade_point is None or enr.grade_point >= 2.0):
                        prereq_met = True
                        break

            if not prereq_met:
                raise PrerequisiteNotMetException(course.code, prereq_code)

        enrollment = Enrollment(
            student_id=data.student_id,
            course_id=data.course_id,
            academic_year=data.academic_year,
            semester=data.semester,
            status="enrolled"
        )
        return self.repo.create(enrollment)

    def update_enrollment(self, enrollment_id: int, data: EnrollmentUpdate) -> Enrollment:
        enr = self.repo.get(enrollment_id)
        if not enr:
            raise EntityNotFoundException("Enrollment", enrollment_id)

        if data.status is not None:
            valid_statuses = {"enrolled", "completed", "dropped", "withdrawn"}
            if data.status.lower() not in valid_statuses:
                raise ValidationException(f"Invalid status '{data.status}'. Must be one of {valid_statuses}")
            enr.status = data.status.lower()

        if data.grade_point is not None:
            enr.grade_point = data.grade_point
        if data.letter_grade is not None:
            enr.letter_grade = data.letter_grade

        return self.repo.update(enr)

    def get_student_enrollments(self, student_id: int) -> List[Enrollment]:
        return self.repo.get_by_student(student_id)

    def get_course_enrollments(self, course_id: int, academic_year: str, semester: int) -> List[Enrollment]:
        return self.repo.get_by_course(course_id, academic_year, semester)
