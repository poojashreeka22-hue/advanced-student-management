"""
Automated Pytest Suite: EduTrack Real University Workflows and Dependency Rules.
Validates business rules across:
- Departments & Faculty hierarchy (HOD eligibility, single HOD rule, department match, transfer resolution)
- Safe deletion guards (departments, faculty, courses, students with active records)
- Prerequisite graph rules (direct self-prerequisite, 2-node circular, transitive circular)
- Student admission & enrollment eligibility (active status, duplicate prevention, passing prerequisites)
- Attendance and Examination grade dependencies (strictly enrolled students only, mark bounds)
- Timetable scheduling dependencies (faculty existence, active status, valid time intervals, room conflicts)
- Financial overpayment guards
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.course import Course
from app.models.student import Student
from app.models.enrollment import Enrollment
from app.models.examination import Examination
from app.models.fee import FeeInvoice


# =============================================================================
# 1. DEPARTMENTS & FACULTY HIERARCHY / HOD GOVERNANCE
# =============================================================================

def test_cannot_create_faculty_for_nonexistent_department(client: TestClient):
    """Faculty assignment requires an existing parent department."""
    res = client.post("/api/v1/faculty", json={
        "employee_id": "EMP_DEPT_MISSING",
        "full_name": "Prof. No Dept",
        "email": "nodept@university.edu",
        "department_id": 99999
    })
    assert res.status_code == 404
    assert "Department with identifier '99999' was not found" in res.json()["detail"]


def test_cannot_create_faculty_for_inactive_department(client: TestClient, db_session: Session):
    """Faculty cannot be assigned to an inactive department."""
    inactive_dept = Department(
        code="INACT_DEPT_1",
        name="Inactive Department 1",
        is_active=False
    )
    db_session.add(inactive_dept)
    db_session.commit()

    res = client.post("/api/v1/faculty", json={
        "employee_id": "EMP_INACT_DEPT",
        "full_name": "Prof. Inactive Member",
        "email": "inact_mem@university.edu",
        "department_id": inactive_dept.id
    })
    assert res.status_code == 400
    assert "Cannot assign faculty to inactive department" in res.json()["detail"]


def test_assign_hod_success(client: TestClient, sample_department: Department):
    """Assigning an active faculty member of the department as HOD succeeds."""
    fac_res = client.post("/api/v1/faculty", json={
        "employee_id": "EMP_HOD_SUCCESS",
        "full_name": "Dr. Katherine Johnson",
        "email": "katherine.johnson@university.edu",
        "department_id": sample_department.id,
        "designation": "Professor"
    })
    assert fac_res.status_code == 201
    fac_id = fac_res.json()["id"]

    hod_res = client.post(f"/api/v1/departments/{sample_department.id}/hod", json={
        "faculty_id": fac_id
    })
    assert hod_res.status_code == 200
    data = hod_res.json()
    assert data["hod_faculty_id"] == fac_id
    assert data["head_of_department"] == "Dr. Katherine Johnson"


def test_cannot_assign_hod_from_different_department(client: TestClient, sample_department: Department, db_session: Session):
    """HOD candidate must belong to the department they are assigned to lead."""
    other_dept = Department(code="MATH_DEPT", name="Mathematics Department", is_active=True)
    db_session.add(other_dept)
    db_session.commit()

    # Create faculty in MATH_DEPT
    fac_res = client.post("/api/v1/faculty", json={
        "employee_id": "EMP_MATH_FAC",
        "full_name": "Dr. Carl Gauss",
        "email": "gauss@university.edu",
        "department_id": other_dept.id,
        "designation": "Professor"
    })
    assert fac_res.status_code == 201
    math_fac_id = fac_res.json()["id"]

    # Try assigning Math faculty as HOD of Computer Science department
    hod_res = client.post(f"/api/v1/departments/{sample_department.id}/hod", json={
        "faculty_id": math_fac_id
    })
    assert hod_res.status_code == 400
    assert "Faculty belongs to department" in hod_res.json()["detail"]


def test_cannot_assign_inactive_faculty_as_hod(client: TestClient, sample_department: Department, db_session: Session):
    """Inactive or terminated faculty members cannot be appointed as HOD."""
    inact_fac = Faculty(
        employee_id="EMP_INACT_HOD",
        full_name="Dr. Inactive Lead",
        email="inact_hod@university.edu",
        department_id=sample_department.id,
        is_active=False
    )
    db_session.add(inact_fac)
    db_session.commit()

    hod_res = client.post(f"/api/v1/departments/{sample_department.id}/hod", json={
        "faculty_id": inact_fac.id
    })
    assert hod_res.status_code == 400
    assert "status is inactive or terminated" in hod_res.json()["detail"]


def test_cannot_assign_faculty_as_hod_of_multiple_departments(client: TestClient, sample_department: Department, db_session: Session):
    """A faculty member cannot simultaneously serve as HOD of multiple departments."""
    dept2 = Department(code="PHYS_DEPT", name="Physics Department", is_active=True)
    db_session.add(dept2)
    db_session.commit()

    fac_res = client.post("/api/v1/faculty", json={
        "employee_id": "EMP_DUAL_HOD",
        "full_name": "Dr. Dual Leader",
        "email": "dual_lead@university.edu",
        "department_id": sample_department.id
    })
    fac_id = fac_res.json()["id"]

    # Assign to dept 1
    res1 = client.post(f"/api/v1/departments/{sample_department.id}/hod", json={"faculty_id": fac_id})
    assert res1.status_code == 200

    # Transfer faculty to dept 2 without clearing HOD, then assign to dept 2
    # But before transfer, directly trying to assign to dept 2 will fail on department match
    # Transfer:
    client.put(f"/api/v1/faculty/{fac_id}", json={"department_id": dept2.id})
    # After transfer, old dept HOD is vacated, now assigning to dept2 succeeds
    res2 = client.post(f"/api/v1/departments/{dept2.id}/hod", json={"faculty_id": fac_id})
    assert res2.status_code == 200

    # Old dept HOD should now be vacant
    d1_check = client.get(f"/api/v1/departments/{sample_department.id}").json()
    assert d1_check["hod_faculty_id"] is None


def test_cannot_deactivate_faculty_serving_as_hod(client: TestClient, sample_department: Department):
    """Deactivating an active HOD is blocked until the HOD role is vacated or reassigned."""
    fac_res = client.post("/api/v1/faculty", json={
        "employee_id": "EMP_DEACT_HOD",
        "full_name": "Dr. Active Head",
        "email": "active_head@university.edu",
        "department_id": sample_department.id
    })
    fac_id = fac_res.json()["id"]

    client.post(f"/api/v1/departments/{sample_department.id}/hod", json={"faculty_id": fac_id})

    # Attempt to deactivate faculty
    deact_res = client.put(f"/api/v1/faculty/{fac_id}", json={"is_active": False})
    assert deact_res.status_code == 400
    assert "while they are serving as Head of Department" in deact_res.json()["detail"]


def test_cannot_delete_department_with_faculty(client: TestClient, sample_department: Department):
    """Department deletion is blocked when dependent faculty members exist."""
    client.post("/api/v1/faculty", json={
        "employee_id": "EMP_DEP_SAFE",
        "full_name": "Dr. Safe Faculty",
        "email": "safe_fac@university.edu",
        "department_id": sample_department.id
    })
    del_res = client.delete(f"/api/v1/departments/{sample_department.id}")
    assert del_res.status_code == 400
    assert "associated faculty member(s)" in del_res.json()["detail"]


def test_cannot_delete_faculty_serving_as_hod(client: TestClient, sample_department: Department):
    """Faculty deletion is blocked when the faculty is currently serving as HOD."""
    fac_res = client.post("/api/v1/faculty", json={
        "employee_id": "EMP_DEL_HOD",
        "full_name": "Dr. Undeletable Head",
        "email": "undel_head@university.edu",
        "department_id": sample_department.id
    })
    fac_id = fac_res.json()["id"]
    client.post(f"/api/v1/departments/{sample_department.id}/hod", json={"faculty_id": fac_id})

    del_res = client.delete(f"/api/v1/faculty/{fac_id}")
    assert del_res.status_code == 400
    assert "currently serving as Head of Department" in del_res.json()["detail"]


# =============================================================================
# 2. COURSES & PREREQUISITE CYCLES
# =============================================================================

def test_cannot_set_course_self_prerequisite(client: TestClient, sample_department: Department):
    """A course cannot have itself as its own prerequisite."""
    c_res = client.post("/api/v1/courses", json={
        "code": "CRS_SELF_PRE",
        "title": "Self Prereq Course",
        "department_id": sample_department.id
    })
    c_id = c_res.json()["id"]

    up_res = client.put(f"/api/v1/courses/{c_id}", json={
        "prerequisite_id": c_id
    })
    assert up_res.status_code == 400
    assert "A course cannot have itself as a prerequisite" in up_res.json()["detail"]


def test_cannot_set_direct_circular_prerequisite(client: TestClient, sample_department: Department):
    """Direct circular prerequisite (A -> B -> A) is detected and rejected."""
    # Create Course A
    cA = client.post("/api/v1/courses", json={
        "code": "CRS_CIRC_A",
        "title": "Circular Course A",
        "department_id": sample_department.id
    }).json()["id"]

    # Create Course B with prerequisite Course A
    cB = client.post("/api/v1/courses", json={
        "code": "CRS_CIRC_B",
        "title": "Circular Course B",
        "department_id": sample_department.id,
        "prerequisite_id": cA
    }).json()["id"]

    # Try setting Course A's prerequisite to Course B (Cycle: A -> B -> A)
    up_res = client.put(f"/api/v1/courses/{cA}", json={
        "prerequisite_id": cB
    })
    assert up_res.status_code == 400
    assert "Circular prerequisite dependency detected" in up_res.json()["detail"]


def test_cannot_set_transitive_circular_prerequisite(client: TestClient, sample_department: Department):
    """Transitive circular prerequisite (A -> B -> C -> A) is detected and rejected."""
    # A -> B -> C
    cA = client.post("/api/v1/courses", json={
        "code": "CRS_TRANS_A", "title": "Course A", "department_id": sample_department.id
    }).json()["id"]

    cB = client.post("/api/v1/courses", json={
        "code": "CRS_TRANS_B", "title": "Course B", "department_id": sample_department.id, "prerequisite_id": cA
    }).json()["id"]

    cC = client.post("/api/v1/courses", json={
        "code": "CRS_TRANS_C", "title": "Course C", "department_id": sample_department.id, "prerequisite_id": cB
    }).json()["id"]

    # Now attempt to set Course A's prerequisite to Course C (Cycle: A -> B -> C -> A)
    res = client.put(f"/api/v1/courses/{cA}", json={"prerequisite_id": cC})
    assert res.status_code == 400
    assert "Circular prerequisite dependency detected" in res.json()["detail"]


def test_cannot_delete_course_with_dependent_courses(client: TestClient, sample_department: Department):
    """Course cannot be deleted if another active course depends on it as a prerequisite."""
    c_base = client.post("/api/v1/courses", json={
        "code": "CRS_PARENT_PR", "title": "Prereq Course", "department_id": sample_department.id
    }).json()["id"]

    client.post("/api/v1/courses", json={
        "code": "CRS_CHILD_PR", "title": "Advanced Course", "department_id": sample_department.id, "prerequisite_id": c_base
    })

    del_res = client.delete(f"/api/v1/courses/{c_base}")
    assert del_res.status_code == 400
    assert "It is a prerequisite for" in del_res.json()["detail"]


# =============================================================================
# 3. STUDENT ADMISSION & COURSE ENROLLMENT DEPENDENCIES
# =============================================================================

def test_cannot_enroll_inactive_student(client: TestClient, sample_course: Course, sample_department: Department):
    """Suspended or inactive students cannot enroll in courses."""
    stu_res = client.post("/students", json={
        "full_name": "Suspended Student",
        "register_number": "REG_SUSP_001",
        "email": "suspended@univ.edu",
        "phone_number": "9876543210",
        "department": sample_department.name,
        "academic_year": "1st Year",
        "status": "suspended"
    })
    assert stu_res.status_code == 201
    stu_id = stu_res.json()["id"]

    enr_res = client.post("/api/v1/enrollments", json={
        "student_id": stu_id,
        "course_id": sample_course.id,
        "academic_year": "2026-2027",
        "semester": 1
    })
    assert enr_res.status_code == 400
    assert "Student must be active" in enr_res.json()["detail"]


def test_cannot_enroll_twice_in_same_course(client: TestClient, sample_course: Course, sample_department: Department):
    """Students cannot be enrolled concurrently in the same course."""
    stu_res = client.post("/students", json={
        "full_name": "Enrolled Student",
        "register_number": "REG_DUP_ENR",
        "email": "dupenr@univ.edu",
        "phone_number": "9876543210",
        "department": sample_department.name,
        "academic_year": "1st Year",
        "status": "active"
    })
    assert stu_res.status_code == 201
    stu_id = stu_res.json()["id"]

    # First enrollment succeeds
    e1 = client.post("/api/v1/enrollments", json={
        "student_id": stu_id,
        "course_id": sample_course.id,
        "academic_year": "2026-2027",
        "semester": 1
    })
    assert e1.status_code == 201

    # Second enrollment in another semester while still actively enrolled is rejected
    e2 = client.post("/api/v1/enrollments", json={
        "student_id": stu_id,
        "course_id": sample_course.id,
        "academic_year": "2026-2027",
        "semester": 2
    })
    assert e2.status_code == 400
    assert "actively enrolled" in e2.json()["detail"].lower()


def test_cannot_delete_student_with_active_enrollments(client: TestClient, sample_course: Course, sample_department: Department):
    """Student with active course enrollments cannot be deleted."""
    stu_res = client.post("/students", json={
        "full_name": "Active Enrolled Student",
        "register_number": "REG_ACT_ENR",
        "email": "act_enr@univ.edu",
        "phone_number": "9876543210",
        "department": sample_department.name,
        "academic_year": "1st Year",
        "status": "active"
    })
    assert stu_res.status_code == 201
    stu_id = stu_res.json()["id"]

    client.post("/api/v1/enrollments", json={
        "student_id": stu_id,
        "course_id": sample_course.id,
        "academic_year": "2026-2027",
        "semester": 1
    })

    del_res = client.delete(f"/students/{stu_id}")
    assert del_res.status_code == 400
    assert "active course enrollment" in del_res.json()["detail"]


# =============================================================================
# 4. ATTENDANCE & EXAMINATION WORKFLOWS
# =============================================================================

def test_cannot_record_attendance_for_non_enrolled_student(client: TestClient, sample_course: Course, sample_department: Department):
    """Attendance can only be recorded for students legitimately enrolled in the course."""
    stu_res = client.post("/students", json={
        "full_name": "Not Enrolled Student",
        "register_number": "REG_NOT_ENR",
        "email": "not_enr@univ.edu",
        "phone_number": "9876543210",
        "department": sample_department.name,
        "academic_year": "1st Year",
        "status": "active"
    })
    assert stu_res.status_code == 201
    stu_id = stu_res.json()["id"]

    att_res = client.post("/api/v1/attendance", json={
        "student_id": stu_id,
        "course_id": sample_course.id,
        "session_date": "2026-10-25",
        "slot_number": 1,
        "status": "present"
    })
    assert att_res.status_code == 400
    assert "is not actively enrolled" in att_res.json()["detail"]


def test_cannot_record_grade_for_non_enrolled_student(client: TestClient, sample_course: Course, sample_department: Department):
    """Grades can only be recorded for students legitimately enrolled in the examination's course."""
    stu_res = client.post("/students", json={
        "full_name": "No Grade Student",
        "register_number": "REG_NO_GRD",
        "email": "nogrd@univ.edu",
        "phone_number": "9876543210",
        "department": sample_department.name,
        "academic_year": "1st Year",
        "status": "active"
    })
    assert stu_res.status_code == 201
    stu_id = stu_res.json()["id"]

    exam_res = client.post("/api/v1/examinations", json={
        "course_id": sample_course.id,
        "title": "Midterm Exam",
        "exam_type": "midterm",
        "max_marks": 100.0,
        "weightage_percent": 30.0,
        "semester": 1
    })
    exam_id = exam_res.json()["id"]

    grd_res = client.post("/api/v1/grades", json={
        "examination_id": exam_id,
        "student_id": stu_id,
        "marks_obtained": 85.0
    })
    assert grd_res.status_code == 400
    assert "is not enrolled in the course for Examination" in grd_res.json()["detail"]


def test_cannot_record_grade_exceeding_max_marks(client: TestClient, sample_course: Course, sample_department: Department):
    """Marks obtained cannot exceed examination max marks."""
    stu_res = client.post("/students", json={
        "full_name": "Marks Test Student",
        "register_number": "REG_MARKS_01",
        "email": "marks_stu@univ.edu",
        "phone_number": "9876543210",
        "department": sample_department.name,
        "academic_year": "1st Year",
        "status": "active"
    })
    assert stu_res.status_code == 201
    stu_id = stu_res.json()["id"]

    # Enroll student
    client.post("/api/v1/enrollments", json={
        "student_id": stu_id, "course_id": sample_course.id, "academic_year": "2026-2027", "semester": 1
    })

    exam_res = client.post("/api/v1/examinations", json={
        "course_id": sample_course.id,
        "title": "Quiz 1",
        "exam_type": "quiz",
        "max_marks": 20.0,
        "weightage_percent": 10.0,
        "semester": 1
    })
    exam_id = exam_res.json()["id"]

    grd_res = client.post("/api/v1/grades", json={
        "examination_id": exam_id,
        "student_id": stu_id,
        "marks_obtained": 25.0  # Exceeds 20.0
    })
    assert grd_res.status_code == 400
    assert "cannot be negative or exceed exam maximum marks" in grd_res.json()["detail"]


# =============================================================================
# 5. TIMETABLE & FINANCIAL DEPENDENCIES
# =============================================================================

def test_cannot_schedule_slot_for_inactive_faculty(client: TestClient, sample_course: Course, sample_department: Department, db_session: Session):
    """Cannot assign inactive faculty to timetable slots."""
    room_res = client.post("/api/v1/timetable/classrooms", json={
        "room_number": "HALL_INACT_FAC",
        "building": "Main",
        "capacity": 50
    })
    room_id = room_res.json()["id"]

    inact_fac = Faculty(
        employee_id="FAC_INACT_TT",
        full_name="Dr. TT Inactive",
        email="tt_inact@univ.edu",
        department_id=sample_department.id,
        is_active=False
    )
    db_session.add(inact_fac)
    db_session.commit()

    slot_res = client.post("/api/v1/timetable/slots", json={
        "course_id": sample_course.id,
        "faculty_id": inact_fac.id,
        "classroom_id": room_id,
        "day_of_week": "Monday",
        "start_time": "10:00",
        "end_time": "11:30"
    })
    assert slot_res.status_code == 400
    assert "inactive faculty member" in slot_res.json()["detail"]


def test_cannot_overpay_fee_invoice(client: TestClient, sample_department: Department):
    """Overpayment beyond the outstanding fee invoice balance is rejected."""
    stu_res = client.post("/students", json={
        "full_name": "Fee Test Student",
        "register_number": "REG_FEE_OVER",
        "email": "fee_over@univ.edu",
        "phone_number": "9876543210",
        "department": sample_department.name,
        "academic_year": "1st Year",
        "status": "active"
    })
    assert stu_res.status_code == 201
    stu_id = stu_res.json()["id"]

    inv_res = client.post("/api/v1/fees/invoices", json={
        "student_id": stu_id,
        "academic_year": "2026-2027",
        "semester": 1,
        "title": "Semester Tuition",
        "amount": 1000.0,
        "waiver_amount": 200.0,
        "due_date": "2026-11-30"
    })
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # Outstanding balance = 1000 - 200 = 800. Trying to pay 850 should be rejected.
    pay_res = client.post("/api/v1/fees/payments", json={
        "invoice_id": inv_id,
        "amount_paid": 850.0,
        "payment_method": "online",
        "payment_date": "2026-10-25"
    })
    assert pay_res.status_code == 400
    assert "exceeds outstanding balance" in pay_res.json()["detail"]
