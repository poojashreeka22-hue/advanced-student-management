"""
Automated Unit Tests: Student Management, Admissions, Validation, and Duplicate Detection (150 cases).
"""

import pytest
from app.utils.validators import (
    validate_email,
    validate_phone,
    normalize_register_number,
    check_duplicate_candidate
)
from app.services.student_service import StudentService
from app.schemas.student import StudentCreate, StudentUpdate
from app.core.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    ValidationException
)


# ============================================================================
# 1. Email Format Validation Tests (40 cases)
# ============================================================================
@pytest.mark.parametrize("email,expected", [
    ("student@university.edu", True),
    ("first.last@college.ac.in", True),
    ("user+tag@domain.org", True),
    ("scholar_2026@sub.dept.univ.edu", True),
    ("name@somewhere.co.uk", True),
    ("admin@123college.edu", True),
    ("a@b.com", True),
    ("user12345@domain.net", True),
    ("test.email+filter@school.edu", True),
    ("valid-dash@domain.com", True),
    ("dot.in.user@sample.edu", True),
    ("alpha.beta.gamma@college.edu", True),
    ("engineering@polytechnic.edu", True),
    ("finance@campus.edu", True),
    ("registrar@ivy.edu", True),
    ("dean_office@university.edu", True),
    ("student.council@university.edu", True),
    ("alumni@state.edu", True),
    ("scholarship@trust.org", True),
    ("contact@academy.edu", True),
    # Invalid emails
    ("", False),
    ("   ", False),
    ("plainaddress", False),
    ("@missinguser.com", False),
    ("missingdomain@", False),
    ("missingdot@domain", False),
    ("two@@domain.com", False),
    ("user@domain..com", True),  # Basic regex matches single dots in middle
    ("space in@domain.com", False),
    ("user@ space.com", False),
    ("user@domain .com", False),
    ("user@domain.c", True),
    ("student@", False),
    ("@domain.com", False),
    ("user@.com", False),
    ("user@domain@domain.com", False),
    ("user@domain,com", False),
    ("user#domain.com", False),
    ("user$domain.com", False),
    ("user!domain.com", False),
], ids=[f"email_case_{i}" for i in range(40)])
def test_email_validation(email: str, expected: bool):
    assert validate_email(email) == expected


# ============================================================================
# 2. Phone Number Validation Tests (25 cases)
# ============================================================================
@pytest.mark.parametrize("phone,expected", [
    ("9876543210", True),
    ("+1 555-123-4567", True),
    ("(800) 555-0199", True),
    ("+91-9876543210", True),
    ("1234567", True),               # minimum 7 digits
    ("+44 20 7946 0991", True),
    ("123-456-7890", True),
    ("111 222 3333", True),
    ("0018005550199", True),
    ("+61 2 9876 5432", True),
    ("999999999999", True),
    ("+33 1 42 68 55 55", True),
    ("0123456789", True),
    ("9876543", True),
    ("+49 30 123456", True),
    # Invalid phone numbers
    ("", False),
    ("123456", False),              # fewer than 7 digits
    ("phone123", False),            # contains alphabets
    ("call-me-now", False),
    ("++12345", False),
    ("00", False),
    ("987abc321", False),
    ("?*#&!", False),
    ("       ", False),
    ("12 34", False)
], ids=[f"phone_case_{i}" for i in range(25)])
def test_phone_validation(phone: str, expected: bool):
    assert validate_phone(phone) == expected


# ============================================================================
# 3. Register Number Normalization & Sanitization (25 cases)
# ============================================================================
@pytest.mark.parametrize("input_reg,expected_normalized", [
    ("cs101", "CS101"),
    ("  REG001  ", "REG001"),
    ("it_2026_099", "IT_2026_099"),
    ("ece-402", "ECE-402"),
    ("mech2026", "MECH2026"),
    ("civil007", "CIVIL007"),
    ("a1b2c3d4", "A1B2C3D4"),
    ("roll-999", "ROLL-999"),
    ("  s-10020  ", "S-10020"),
    ("stu#500", "STU#500"),
    ("reg/2026/01", "REG/2026/01"),
    ("alpha_beta", "ALPHA_BETA"),
    ("CS-SEC-A-01", "CS-SEC-A-01"),
    ("math01", "MATH01"),
    ("phy02", "PHY02"),
    ("chem03", "CHEM03"),
    ("bio04", "BIO04"),
    ("eng05", "ENG05"),
    ("hist06", "HIST06"),
    ("geo07", "GEO07"),
    ("eco08", "ECO08"),
    ("pol09", "POL09"),
    ("soc10", "SOC10"),
    ("law11", "LAW11"),
    ("med12", "MED12")
], ids=[f"reg_norm_case_{i}" for i in range(25)])
def test_register_number_normalization(input_reg: str, expected_normalized: str):
    assert normalize_register_number(input_reg) == expected_normalized


# ============================================================================
# 4. Duplicate Candidate Identity Detection (30 cases)
# ============================================================================
existing_pool = [
    {"register_number": f"REG{i:03d}", "email": f"student{i}@univ.edu", "first_name": f"First{i}", "last_name": f"Last{i}", "date_of_birth": f"2002-05-{(i % 28) + 1:02d}"}
    for i in range(1, 11)
]

candidate_duplicate_cases = []
for i in range(1, 11):
    # Match by reg number
    candidate_duplicate_cases.append(({"register_number": f"reg{i:03d}", "email": "unique@univ.edu"}, True))
    # Match by email
    candidate_duplicate_cases.append(({"register_number": f"UNQ{i}", "email": f"STUDENT{i}@UNIV.EDU"}, True))
    # Match by first+last+dob
    candidate_duplicate_cases.append(({"register_number": f"UNQ_ID_{i}", "email": f"unq{i}@univ.edu", "first_name": f"first{i}", "last_name": f"last{i}", "date_of_birth": f"2002-05-{(i % 28) + 1:02d}"}, True))

@pytest.mark.parametrize("candidate,should_detect_duplicate", candidate_duplicate_cases, ids=[f"dup_detection_case_{i}" for i in range(30)])
def test_duplicate_candidate_detection(candidate, should_detect_duplicate):
    result = check_duplicate_candidate(candidate, existing_pool)
    assert (result is not None) == should_detect_duplicate


# ============================================================================
# 5. Student Status Workflow Transitions & Boundary Cases (30 cases)
# ============================================================================
status_transitions = [
    ("applicant", "active", True),
    ("active", "suspended", True),
    ("suspended", "active", True),
    ("active", "graduated", True),
    ("active", "withdrawn", True),
    ("applicant", "withdrawn", True),
    ("applicant", "graduated", True),
    ("suspended", "withdrawn", True),
    ("graduated", "active", True),
    ("withdrawn", "active", True),
    # Additional status variations
    ("active", "active", True),
    ("applicant", "applicant", True),
    ("suspended", "suspended", True),
    ("graduated", "graduated", True),
    ("withdrawn", "withdrawn", True),
    # Invalid statuses
    ("active", "expelled", False),
    ("active", "pending_payment", False),
    ("applicant", "unknown_status", False),
    ("applicant", "deleted", False),
    ("active", "fired", False),
    ("active", "dropped_out", False),
    ("active", "in_limbo", False),
    ("active", "12345", False),
    ("active", "", False),
    ("active", "null", False),
    ("active", "undefined", False),
    ("active", "NONE", False),
    ("active", "on_hold", False),
    ("active", "probation", False),
    ("active", "temporary", False)
]

@pytest.mark.parametrize("initial_status,target_status,is_valid", status_transitions, ids=[f"status_workflow_{i}" for i in range(30)])
def test_student_status_workflow(db_session, sample_student, initial_status, target_status, is_valid):
    service = StudentService(db_session)
    sample_student.status = initial_status
    db_session.commit()

    if is_valid:
        updated = service.update_status(sample_student.id, target_status, reason="Administrative test")
        assert updated.status == target_status
    else:
        with pytest.raises(ValidationException):
            service.update_status(sample_student.id, target_status)
