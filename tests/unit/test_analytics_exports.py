"""
Automated Unit Tests: Institutional Analytics, Department Rollups, and Safe CSV Exports (50 cases).
"""

import pytest
from app.utils.csv_export import sanitize_csv_cell, generate_safe_csv
from app.services.analytics_service import AnalyticsService
from app.services.student_service import StudentService
from app.schemas.student import StudentCreate


# ============================================================================
# 1. CSV Formula Injection Defense and Sanitization (30 cases)
# ============================================================================
dangerous_cells = [
    ("=1+1", "'=1+1"),
    ("=SUM(A1:A10)", "'=SUM(A1:A10)"),
    ("=cmd|'/C calc'!A0", "'=cmd|'/C calc'!A0"),
    ("+2+3", "'+2+3"),
    ("-5-6", "'-5-6"),
    ("@SUM(B1:B5)", "'@SUM(B1:B5)"),
    ("\tTabSeparated", "'\tTabSeparated"),
    ("\rCarriageReturn", "'\rCarriageReturn"),
    ("=IMPORTXML('http://evil.com')", "'=IMPORTXML('http://evil.com')"),
    ("+HYPERLINK('http://evil.com')", "'+HYPERLINK('http://evil.com')"),
    ("=cmd|'/c powershell'!'A1'", "'=cmd|'/c powershell'!'A1'"),
    ("-12345", "'-12345"),
    ("+98765", "'+98765"),
    ("@alert(1)", "'@alert(1)"),
    ("=A1+B1", "'=A1+B1"),
    # Benign strings should not be modified
    ("Normal Name", "Normal Name"),
    ("student@university.edu", "student@university.edu"),
    ("CS101", "CS101"),
    ("12345", "12345"),
    ("Electronics & Communication", "Electronics & Communication"),
    ("Grade: A+", "Grade: A+"),
    ("Dr. Ada Lovelace", "Dr. Ada Lovelace"),
    ("Turing Hall, Room 101", "Turing Hall, Room 101"),
    ("John Doe Jr.", "John Doe Jr."),
    ("Spring 2026", "Spring 2026"),
    ("Valid-String-123", "Valid-String-123"),
    ("100.00%", "100.00%"),
    ("Active", "Active"),
    ("Paid in Full", "Paid in Full"),
    ("9876543210", "9876543210")
]

@pytest.mark.parametrize("raw_input,expected_sanitized", dangerous_cells, ids=[f"csv_sanitize_{i}" for i in range(30)])
def test_csv_injection_sanitization(raw_input, expected_sanitized):
    assert sanitize_csv_cell(raw_input) == expected_sanitized


# ============================================================================
# 2. Analytics Aggregation Metrics (20 cases)
# ============================================================================
analytics_dept_cases = [(f"Dept_{i}", i) for i in range(1, 21)]

@pytest.mark.parametrize("dept_name,count", analytics_dept_cases, ids=[f"analytics_rollup_{i}" for i in range(20)])
def test_analytics_department_aggregation(db_session, dept_name, count):
    stu_service = StudentService(db_session)
    analytics_service = AnalyticsService(db_session)

    # Admit student in department
    student = stu_service.create_student(StudentCreate(
        full_name=f"Analytics Student {count}",
        register_number=f"REG_AN_{count}",
        email=f"an_{count}@univ.edu",
        phone_number="9876543210",
        department=dept_name,
        academic_year="1st Year"
    ))

    stats = analytics_service.get_legacy_stats()
    assert dept_name in stats.department_counts
    assert stats.department_counts[dept_name] >= 1
