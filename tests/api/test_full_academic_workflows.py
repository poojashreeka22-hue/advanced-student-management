"""
End-to-End API Integration Tests for Complete Academic Workflows and Endpoints.
Covers Auth, Student Dossier, Faculty, Courses, Exams, Transcripts, Fee Payments, Timetables, and CSV Reports.
"""

import pytest
from fastapi.testclient import TestClient


def test_auth_workflow_and_me(client: TestClient):
    """Test user registration, login, and /me endpoint."""
    user_data = {
        "username": "workflow_user",
        "email": "workflow_user@test.edu",
        "full_name": "Workflow Specialist",
        "password": "Password@123",
        "role": "admin"
    }
    # Register
    reg_res = client.post("/api/v1/auth/register", json=user_data)
    assert reg_res.status_code == 201
    assert reg_res.json()["username"] == "workflow_user"

    # Login
    login_res = client.post("/api/v1/auth/login", json={"username": "workflow_user", "password": "Password@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token is not None

    # Get /me
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "workflow_user@test.edu"


def test_department_and_faculty_crud_api(client: TestClient):
    """Test department creation, listing, faculty creation and retrieval."""
    dept_res = client.post("/api/v1/departments", json={
        "code": "BIO_TECH",
        "name": "Biotechnology",
        "head_of_department": "Dr. Watson",
        "building": "Darwin Lab",
        "budget": 350000.0
    })
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["id"]

    # Get department
    get_dept = client.get(f"/api/v1/departments/{dept_id}")
    assert get_dept.status_code == 200
    assert get_dept.json()["code"] == "BIO_TECH"

    # List departments
    list_dept = client.get("/api/v1/departments")
    assert list_dept.status_code == 200
    assert len(list_dept.json()) >= 1

    # Create faculty
    fac_res = client.post("/api/v1/faculty", json={
        "employee_id": "EMP_BIO_01",
        "full_name": "Dr. Rosalind Franklin",
        "email": "r.franklin@test.edu",
        "department_id": dept_id,
        "designation": "Professor",
        "specialization": "Crystallography"
    })
    assert fac_res.status_code == 201
    fac_id = fac_res.json()["id"]

    # Get faculty
    get_fac = client.get(f"/api/v1/faculty/{fac_id}")
    assert get_fac.status_code == 200
    assert get_fac.json()["employee_id"] == "EMP_BIO_01"


def test_course_crud_and_enrollment_workflow_api(client: TestClient, sample_department):
    """Test course creation, enrollment, and attendance via API."""
    crs_res = client.post("/api/v1/courses", json={
        "code": "BIO101",
        "title": "Molecular Biology",
        "credits": 4,
        "department_id": sample_department.id,
        "max_capacity": 30,
        "semester": 1
    })
    assert crs_res.status_code == 201
    course_id = crs_res.json()["id"]

    # Create student
    stu_res = client.post("/students", json={
        "full_name": "Charles Darwin",
        "register_number": "BIO2026001",
        "email": "charles.darwin@test.edu",
        "phone_number": "9876543210",
        "department": sample_department.name,
        "academic_year": "1st Year",
        "status": "active"
    })
    assert stu_res.status_code == 201
    student_id = stu_res.json()["id"]

    # Enroll student in course
    enr_res = client.post("/api/v1/enrollments", json={
        "student_id": student_id,
        "course_id": course_id,
        "academic_year": "2026-2027",
        "semester": 1
    })
    assert enr_res.status_code == 201

    # Get student enrollments
    get_enrs = client.get(f"/api/v1/enrollments/student/{student_id}")
    assert get_enrs.status_code == 200
    assert len(get_enrs.json()) >= 1

    # Record attendance
    att_res = client.post("/api/v1/attendance", json={
        "student_id": student_id,
        "course_id": course_id,
        "session_date": "2026-10-25",
        "slot_number": 1,
        "status": "present"
    })
    assert att_res.status_code == 201

    # Bulk attendance
    bulk_res = client.post("/api/v1/attendance/bulk", json={
        "course_id": course_id,
        "session_date": "2026-10-26",
        "slot_number": 2,
        "records": [{"student_id": student_id, "status": "present"}]
    })
    assert bulk_res.status_code == 201

    # Overall attendance
    stu_att = client.get(f"/api/v1/attendance/student/{student_id}")
    assert stu_att.status_code == 200
    assert stu_att.json()["attendance_percentage"] == 100.0


def test_examination_grades_and_transcript_api(client: TestClient, sample_student, sample_course):
    """Test exam scheduling, marks entry, amendment, and academic transcript."""
    # 1. Schedule Examination
    exam_res = client.post("/api/v1/examinations", json={
        "course_id": sample_course.id,
        "title": "Final Examination",
        "exam_type": "final",
        "max_marks": 100.0,
        "weightage_percent": 100.0,
        "semester": 1
    })
    assert exam_res.status_code == 201
    exam_id = exam_res.json()["id"]

    # 2. Enter Grade
    grd_res = client.post("/api/v1/grades", json={
        "examination_id": exam_id,
        "student_id": sample_student.id,
        "marks_obtained": 94.0,
        "is_absent": False
    })
    assert grd_res.status_code == 201
    grade_id = grd_res.json()["id"]
    assert grd_res.json()["letter_grade"] == "A+"

    # 3. Amend Grade
    amend_res = client.patch(f"/api/v1/grades/{grade_id}", json={
        "marks_obtained": 96.0,
        "amendment_reason": "Extra credit recalculation confirmed"
    })
    assert amend_res.status_code == 200
    assert amend_res.json()["marks_obtained"] == 96.0

    # 4. Generate Academic Transcript
    trans_res = client.get(f"/api/v1/grades/student/{sample_student.id}/transcript")
    assert trans_res.status_code == 200
    data = trans_res.json()
    assert data["student_name"] == sample_student.full_name


def test_fee_invoice_payment_and_dossier_api(client: TestClient, sample_student):
    """Test generating invoices, processing payments, and retrieving the student dossier."""
    # Create invoice
    inv_res = client.post("/api/v1/fees/invoices", json={
        "student_id": sample_student.id,
        "title": "Spring Tuition 2026",
        "amount": 2000.0,
        "waiver_amount": 200.0,
        "due_date": "2026-11-30"
    })
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # Record partial payment
    pay_res = client.post("/api/v1/fees/payments", json={
        "invoice_id": inv_id,
        "amount_paid": 800.0,
        "payment_method": "card"
    })
    assert pay_res.status_code == 201

    # Student fee overview
    fee_overview = client.get(f"/api/v1/fees/invoices/student/{sample_student.id}")
    assert fee_overview.status_code == 200
    assert len(fee_overview.json()) >= 1
    assert fee_overview.json()[0]["balance_due"] == 1000.0

    # Complete student dossier
    dossier_res = client.get(f"/api/v1/students/{sample_student.id}/dossier")
    assert dossier_res.status_code == 200
    dossier = dossier_res.json()
    assert dossier["outstanding_fee_balance"] == 1000.0


def test_timetable_and_classrooms_api(client: TestClient, sample_course):
    """Test creating classrooms and scheduling slots."""
    room_res = client.post("/api/v1/timetable/classrooms", json={
        "room_number": "HALL_WORKFLOW_1",
        "building": "West Wing",
        "capacity": 75,
        "room_type": "lecture_hall"
    })
    assert room_res.status_code == 201
    room_id = room_res.json()["id"]

    # List classrooms
    rooms_list = client.get("/api/v1/timetable/classrooms")
    assert rooms_list.status_code == 200
    assert len(rooms_list.json()) >= 1

    # Schedule slot
    slot_res = client.post("/api/v1/timetable/slots", json={
        "course_id": sample_course.id,
        "faculty_id": 1,
        "classroom_id": room_id,
        "day_of_week": "Wednesday",
        "start_time": "14:00",
        "end_time": "15:30"
    })
    assert slot_res.status_code == 201

    # List slots
    slots_res = client.get("/api/v1/timetable/slots")
    assert slots_res.status_code == 200
    assert len(slots_res.json()) >= 1


def test_analytics_metrics_and_csv_exports(client: TestClient):
    """Test dashboard metrics, department performance, and safe CSV exports."""
    # Metrics
    metrics_res = client.get("/api/v1/analytics/metrics")
    assert metrics_res.status_code == 200
    assert "total_students" in metrics_res.json()

    # Department performance
    dept_perf = client.get("/api/v1/analytics/departments")
    assert dept_perf.status_code == 200

    # Grade distribution
    grd_dist = client.get("/api/v1/analytics/grades")
    assert grd_dist.status_code == 200

    # CSV Exports
    csv_students = client.get("/api/v1/reports/export/students")
    assert csv_students.status_code == 200
    assert "text/csv" in csv_students.headers["content-type"]

    csv_fees = client.get("/api/v1/reports/export/fees")
    assert csv_fees.status_code == 200
    assert "text/csv" in csv_fees.headers["content-type"]

    # Audit logs
    audit_res = client.get("/api/v1/audit")
    assert audit_res.status_code == 200
    assert isinstance(audit_res.json(), list)
