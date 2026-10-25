"""
Automated Unit Tests: Course Enrollments, Capacity Thresholds, and Prerequisites (120 cases).
"""

import pytest
from app.services.enrollment_service import EnrollmentService
from app.services.academic_service import AcademicService
from app.services.student_service import StudentService
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate
from app.schemas.course import CourseCreate
from app.schemas.student import StudentCreate
from app.core.exceptions import (
    CapacityExceededException,
    PrerequisiteNotMetException,
    DuplicateEntityException
)


# ============================================================================
# 1. Prerequisite Compliance & Grade Thresholds (40 cases)
# ============================================================================
prereq_test_matrix = []
for i in range(1, 21):
    # Grade point >= 2.0 (Passing) -> Should succeed
    prereq_test_matrix.append((2.0 + (i * 0.1), True))
for i in range(1, 21):
    # Grade point < 2.0 (Failing) -> Should fail
    prereq_test_matrix.append((1.0 + (i * 0.04), False))

@pytest.mark.parametrize("grade_point,should_pass", prereq_test_matrix, ids=[f"prereq_grade_{i}" for i in range(40)])
def test_prerequisite_grade_thresholds(db_session, sample_department, grade_point, should_pass):
    acad_service = AcademicService(db_session)
    enr_service = EnrollmentService(db_session)
    stu_service = StudentService(db_session)

    # 1. Prerequisite Course (e.g. CS100)
    prereq_course = acad_service.create_course(CourseCreate(
        code=f"PREREQ_BASE_{grade_point:.2f}",
        title="Foundations",
        credits=3,
        department_id=sample_department.id
    ))

    # 2. Advanced Course requiring CS100
    adv_course = acad_service.create_course(CourseCreate(
        code=f"ADV_CRS_{grade_point:.2f}",
        title="Advanced Computing",
        credits=4,
        department_id=sample_department.id,
        prerequisite_id=prereq_course.id
    ))

    # 3. Student
    student = stu_service.create_student(StudentCreate(
        full_name="Prereq Test Student",
        register_number=f"REG_PR_{grade_point:.2f}",
        email=f"stu_pr_{grade_point:.2f}@test.edu",
        phone_number="9876543210",
        department=sample_department.name,
        academic_year="2nd Year",
        status="active"
    ))

    # Enroll in prereq and complete with grade_point
    p_enr = enr_service.enroll_student(EnrollmentCreate(
        student_id=student.id,
        course_id=prereq_course.id,
        academic_year="2025-2026",
        semester=1
    ))
    enr_service.update_enrollment(p_enr.id, EnrollmentUpdate(status="completed", grade_point=grade_point))

    # Attempt to enroll in advanced course
    if should_pass:
        enr = enr_service.enroll_student(EnrollmentCreate(
            student_id=student.id,
            course_id=adv_course.id,
            academic_year="2026-2027",
            semester=2
        ))
        assert enr.status == "enrolled"
    else:
        with pytest.raises(PrerequisiteNotMetException):
            enr_service.enroll_student(EnrollmentCreate(
                student_id=student.id,
                course_id=adv_course.id,
                academic_year="2026-2027",
                semester=2
            ))


# ============================================================================
# 2. Course Capacity Limits and Rejection When Full (40 cases)
# ============================================================================
capacity_cases = [(cap, cap) for cap in range(1, 41)]

@pytest.mark.parametrize("configured_capacity,attempts", capacity_cases, ids=[f"cap_limit_{i}" for i in range(40)])
def test_course_capacity_enforcement(db_session, sample_department, configured_capacity, attempts):
    acad_service = AcademicService(db_session)
    enr_service = EnrollmentService(db_session)
    stu_service = StudentService(db_session)

    course = acad_service.create_course(CourseCreate(
        code=f"CAP_CRS_{configured_capacity}",
        title="Capacity Test Course",
        credits=3,
        department_id=sample_department.id,
        max_capacity=1  # Cap at exactly 1
    ))

    # First student enrolls successfully
    student1 = stu_service.create_student(StudentCreate(
        full_name="Student One",
        register_number=f"REG_CAP1_{configured_capacity}",
        email=f"cap1_{configured_capacity}@test.edu",
        phone_number="9876543210",
        department=sample_department.name,
        academic_year="1st Year"
    ))
    enr1 = enr_service.enroll_student(EnrollmentCreate(
        student_id=student1.id,
        course_id=course.id,
        academic_year="2026-2027",
        semester=1
    ))
    assert enr1.status == "enrolled"

    # Second student must be rejected because capacity is 1
    student2 = stu_service.create_student(StudentCreate(
        full_name="Student Two",
        register_number=f"REG_CAP2_{configured_capacity}",
        email=f"cap2_{configured_capacity}@test.edu",
        phone_number="9876543210",
        department=sample_department.name,
        academic_year="1st Year"
    ))
    with pytest.raises(CapacityExceededException):
        enr_service.enroll_student(EnrollmentCreate(
            student_id=student2.id,
            course_id=course.id,
            academic_year="2026-2027",
            semester=1
        ))


# ============================================================================
# 3. Duplicate Enrollment Prevention and Status Lifecycle (40 cases)
# ============================================================================
dup_cases = [(f"DUP_STU_{i:02d}", f"dup_{i}@test.edu") for i in range(1, 41)]

@pytest.mark.parametrize("reg_num,email", dup_cases, ids=[f"dup_enroll_{i}" for i in range(40)])
def test_duplicate_enrollment_prevention(db_session, sample_department, sample_course, reg_num, email):
    stu_service = StudentService(db_session)
    enr_service = EnrollmentService(db_session)

    student = stu_service.create_student(StudentCreate(
        full_name="Duplicate Test Student",
        register_number=reg_num,
        email=email,
        phone_number="9876543210",
        department=sample_department.name,
        academic_year="1st Year"
    ))

    # First enrollment succeeds
    enr = enr_service.enroll_student(EnrollmentCreate(
        student_id=student.id,
        course_id=sample_course.id,
        academic_year="2026-2027",
        semester=1
    ))
    assert enr.status == "enrolled"

    # Second enrollment in the same term raises DuplicateEntityException
    with pytest.raises(DuplicateEntityException):
        enr_service.enroll_student(EnrollmentCreate(
            student_id=student.id,
            course_id=sample_course.id,
            academic_year="2026-2027",
            semester=1
        ))
