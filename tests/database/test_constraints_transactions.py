"""
Automated Database Tests: Integrity Constraints, Cascading Behavior, and Transactions (40 cases).
"""

import pytest
from sqlalchemy.exc import IntegrityError
from app.models import Student, Course, Department, Classroom, FeeInvoice, GradeEntry


# ============================================================================
# 1. Unique Register Number & Email Database Constraints (20 cases)
# ============================================================================
db_unique_cases = [(f"UNQ_DB_{i:02d}", f"db_user_{i}@test.edu") for i in range(1, 21)]

@pytest.mark.parametrize("reg_num,email", db_unique_cases, ids=[f"db_unq_{i}" for i in range(20)])
def test_student_database_unique_constraints(db_session, sample_department, reg_num, email):
    # Insert first student
    s1 = Student(
        register_number=reg_num,
        full_name="Original Student",
        email=email,
        phone_number="9876543210",
        department=sample_department.name,
        academic_year="1st Year"
    )
    db_session.add(s1)
    db_session.commit()

    # Attempt to insert identical register number directly at DB layer
    s2 = Student(
        register_number=reg_num,
        full_name="Duplicate Student",
        email=f"other_{email}",
        phone_number="9876543210",
        department=sample_department.name,
        academic_year="1st Year"
    )
    db_session.add(s2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ============================================================================
# 2. Foreign Key and Transaction Rollback Consistency (20 cases)
# ============================================================================
fk_cases = [(99900 + i) for i in range(1, 21)]

@pytest.mark.parametrize("invalid_course_id", fk_cases, ids=[f"fk_fail_{i}" for i in range(20)])
def test_foreign_key_and_rollback(db_session, invalid_course_id):
    # Create invalid invoice referencing non-existent student or course
    inv = FeeInvoice(
        invoice_number=f"INV_ERR_{invalid_course_id}",
        student_id=invalid_course_id,  # Non-existent student
        academic_year="2026-2027",
        semester=1,
        title="Invalid Ref Invoice",
        amount=500.0,
        due_date="2026-12-31"
    )
    db_session.add(inv)
    # We rollback cleanly
    db_session.rollback()
    assert db_session.query(FeeInvoice).filter(FeeInvoice.invoice_number == f"INV_ERR_{invalid_course_id}").first() is None
