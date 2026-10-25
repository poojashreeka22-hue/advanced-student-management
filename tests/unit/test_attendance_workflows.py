"""
Automated Unit Tests: Attendance Percentages, Threshold Calculations, and Session Rules (120 cases).
"""

import pytest
from app.utils.calculations import calculate_attendance_percentage
from app.services.attendance_service import AttendanceService
from app.schemas.attendance import AttendanceCreate
from app.core.exceptions import DuplicateEntityException


# ============================================================================
# 1. Attendance Percentage Mathematical Boundary Calculations (40 cases)
# ============================================================================
attendance_calc_cases = []
for p in range(10, 50):
    # p = present count out of 50 total sessions (0 excused, 0 cancelled)
    expected_pct = round((p / 50) * 100.0, 2)
    records = [{"status": "present", "is_cancelled": False}] * p + \
              [{"status": "absent", "is_cancelled": False}] * (50 - p)
    attendance_calc_cases.append((records, expected_pct))

@pytest.mark.parametrize("records,expected_pct", attendance_calc_cases, ids=[f"att_pct_{i}" for i in range(40)])
def test_attendance_percentage_formula(records, expected_pct):
    res = calculate_attendance_percentage(records)
    assert res["attendance_percentage"] == expected_pct


# ============================================================================
# 2. Attendance Shortage Threshold Warnings (< 75% vs >= 75%) (40 cases)
# ============================================================================
shortage_cases = []
for p in range(20, 60):
    # Out of 50 sessions
    pct = (p / 50) * 100.0
    records = [{"status": "present", "is_cancelled": False}] * min(p, 50) + \
              [{"status": "absent", "is_cancelled": False}] * max(0, 50 - p)
    should_warn = pct < 75.0
    shortage_cases.append((records, 75.0, should_warn))

@pytest.mark.parametrize("records,threshold,is_shortage", shortage_cases, ids=[f"shortage_{i}" for i in range(40)])
def test_attendance_shortage_threshold(records, threshold, is_shortage):
    res = calculate_attendance_percentage(records, min_threshold=threshold)
    assert res["is_shortage"] == is_shortage


# ============================================================================
# 3. Duplicate Attendance Session Prevention (40 cases)
# ============================================================================
dup_att_cases = [(f"2026-10-{(i % 28) + 1:02d}", (i % 4) + 1) for i in range(1, 41)]

@pytest.mark.parametrize("session_date,slot_number", dup_att_cases, ids=[f"dup_att_{i}" for i in range(40)])
def test_duplicate_attendance_session_prevention(db_session, sample_student, sample_course, session_date, slot_number):
    att_service = AttendanceService(db_session)

    # First attendance recording succeeds
    rec = att_service.record_attendance(AttendanceCreate(
        student_id=sample_student.id,
        course_id=sample_course.id,
        session_date=session_date,
        slot_number=slot_number,
        status="present"
    ))
    assert rec.status == "present"

    # Second recording for identical session date and slot raises DuplicateEntityException
    with pytest.raises(DuplicateEntityException):
        att_service.record_attendance(AttendanceCreate(
            student_id=sample_student.id,
            course_id=sample_course.id,
            session_date=session_date,
            slot_number=slot_number,
            status="late"
        ))
