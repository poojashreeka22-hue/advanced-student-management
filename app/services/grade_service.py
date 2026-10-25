"""
Examinations, Grading Schemes, and GPA Calculation Service.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.grade_repo import GradeRepository
from app.repositories.audit_repo import AuditRepository
from app.repositories.student_repo import StudentRepository
from app.repositories.course_repo import CourseRepository
from app.repositories.enrollment_repo import EnrollmentRepository
from app.models.examination import Examination
from app.models.grade import GradeEntry
from app.models.enrollment import Enrollment
from app.schemas.examination import ExaminationCreate, ExaminationUpdate
from app.schemas.grade import GradeEntryCreate, GradeEntryUpdate, AcademicTranscript, AcademicTranscriptItem
from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    ValidationException
)
from app.utils.calculations import (
    calculate_letter_grade_and_point,
    calculate_weighted_marks,
    calculate_gpa
)


class GradeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = GradeRepository(db)
        self.audit_repo = AuditRepository(db)
        self.student_repo = StudentRepository(db)
        self.course_repo = CourseRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)

    # Examination CRUD
    def create_examination(self, data: ExaminationCreate) -> Examination:
        if not self.course_repo.get(data.course_id):
            raise EntityNotFoundException("Course", data.course_id)

        exam = Examination(
            course_id=data.course_id,
            title=data.title.strip(),
            exam_type=data.exam_type.lower(),
            exam_date=data.exam_date,
            max_marks=data.max_marks,
            weightage_percent=data.weightage_percent,
            academic_year=data.academic_year,
            semester=data.semester
        )
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def get_examination(self, exam_id: int) -> Examination:
        exam = self.db.query(Examination).filter(Examination.id == exam_id).first()
        if not exam:
            raise EntityNotFoundException("Examination", exam_id)
        return exam

    def get_course_examinations(self, course_id: int) -> List[Examination]:
        return self.db.query(Examination).filter(Examination.course_id == course_id).all()

    # Grade Entries
    def enter_grade(
        self,
        data: GradeEntryCreate,
        graded_by: Optional[str] = None
    ) -> GradeEntry:
        exam = self.get_examination(data.examination_id)
        student = self.student_repo.get(data.student_id)
        if not student:
            raise EntityNotFoundException("Student", data.student_id)

        # Validate student is active
        if student.status != "active":
            raise ValidationException(
                f"Cannot record grades for student #{student.id} with status '{student.status}'. Student must be active."
            )

        # Validate marks against examination maximum marks
        if data.marks_obtained < 0.0 or data.marks_obtained > exam.max_marks:
            raise ValidationException(
                f"Marks obtained ({data.marks_obtained}) cannot be negative or exceed exam maximum marks ({exam.max_marks})"
            )

        # Verify student is enrolled in the course associated with this examination
        enrollment = self.db.query(Enrollment).filter(
            Enrollment.student_id == data.student_id,
            Enrollment.course_id == exam.course_id
        ).first()
        if not enrollment or enrollment.status not in ("enrolled", "completed"):
            raise ValidationException(
                f"Student #{data.student_id} is not enrolled in the course for Examination '{exam.title}'. "
                f"Grades can only be recorded for enrolled students."
            )

        # Duplicate check
        existing = self.repo.find_entry(data.examination_id, data.student_id)
        if existing:
            raise DuplicateEntityException(
                "GradeEntry",
                "student_exam",
                f"Student {data.student_id} already has grades recorded for Exam {data.examination_id}"
            )

        # Derive letter grade
        percentage = (data.marks_obtained / exam.max_marks) * 100.0 if not data.is_absent else 0.0
        derived_letter, _ = calculate_letter_grade_and_point(percentage)

        entry = GradeEntry(
            examination_id=data.examination_id,
            student_id=data.student_id,
            marks_obtained=0.0 if data.is_absent else data.marks_obtained,
            is_absent=data.is_absent,
            letter_grade=data.letter_grade or derived_letter,
            remarks=data.remarks,
            graded_by=graded_by
        )
        created = self.repo.create(entry)

        self.audit_repo.log_event(
            action="GRADE_ENTRY",
            entity_type="Grade",
            entity_id=str(created.id),
            username=graded_by,
            new_values=f"Exam: {exam.title}, Student: {student.full_name}, Marks: {entry.marks_obtained}/{exam.max_marks}"
        )
        return created

    def amend_grade(
        self,
        grade_id: int,
        data: GradeEntryUpdate,
        amended_by: Optional[str] = None
    ) -> GradeEntry:
        entry = self.repo.get(grade_id)
        if not entry:
            raise EntityNotFoundException("GradeEntry", grade_id)

        if not data.amendment_reason or not data.amendment_reason.strip():
            raise ValidationException("An explicit amendment reason is mandatory when altering existing grade records.")

        exam = self.get_examination(entry.examination_id)
        old_marks = entry.marks_obtained

        if data.marks_obtained is not None:
            if data.marks_obtained < 0.0 or data.marks_obtained > exam.max_marks:
                raise ValidationException(
                    f"Marks obtained ({data.marks_obtained}) cannot exceed exam maximum marks ({exam.max_marks})"
                )
            entry.marks_obtained = data.marks_obtained

        if data.is_absent is not None:
            entry.is_absent = data.is_absent
            if data.is_absent:
                entry.marks_obtained = 0.0

        if data.remarks is not None:
            entry.remarks = data.remarks

        entry.amendment_reason = data.amendment_reason.strip()
        entry.graded_by = amended_by

        # Recalculate letter grade
        percentage = (entry.marks_obtained / exam.max_marks) * 100.0 if not entry.is_absent else 0.0
        derived_letter, _ = calculate_letter_grade_and_point(percentage)
        entry.letter_grade = data.letter_grade or derived_letter

        updated = self.repo.update(entry)

        self.audit_repo.log_event(
            action="GRADE_AMEND",
            entity_type="Grade",
            entity_id=str(grade_id),
            username=amended_by,
            old_values=f"Old Marks: {old_marks}",
            new_values=f"New Marks: {entry.marks_obtained}, Reason: {data.amendment_reason}"
        )
        return updated

    def generate_student_transcript(self, student_id: int) -> AcademicTranscript:
        student = self.student_repo.get(student_id)
        if not student:
            raise EntityNotFoundException("Student", student_id)

        enrollments = self.enrollment_repo.get_by_student(student_id)
        transcript_items: List[AcademicTranscriptItem] = []
        gpa_courses_data: List[Dict[str, Any]] = []

        for enr in enrollments:
            course = self.course_repo.get(enr.course_id)
            if not course:
                continue

            # Find all exam grades for this student and this course
            exams = self.get_course_examinations(course.id)
            exam_records = []
            for ex in exams:
                gr = self.repo.find_entry(ex.id, student_id)
                if gr:
                    exam_records.append({
                        "marks_obtained": gr.marks_obtained,
                        "max_marks": ex.max_marks,
                        "weightage_percent": ex.weightage_percent
                    })

            course_percentage = calculate_weighted_marks(exam_records)
            letter, point = calculate_letter_grade_and_point(course_percentage)

            transcript_items.append(
                AcademicTranscriptItem(
                    course_code=course.code,
                    course_title=course.title,
                    credits=course.credits,
                    marks_percentage=course_percentage,
                    letter_grade=letter,
                    grade_point=point
                )
            )
            gpa_courses_data.append({"credits": course.credits, "grade_point": point})

        cumulative_gpa = calculate_gpa(gpa_courses_data)
        total_credits = sum(item.credits for item in transcript_items)

        # Update cached GPA on student record
        student.gpa = cumulative_gpa
        self.student_repo.update(student)

        return AcademicTranscript(
            student_id=student.id,
            student_name=student.full_name,
            register_number=student.register_number,
            department=student.department,
            academic_year=student.academic_year,
            semester=student.semester,
            items=transcript_items,
            total_credits=total_credits,
            gpa=cumulative_gpa
        )
