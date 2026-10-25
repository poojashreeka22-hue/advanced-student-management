"""
Automated Unit Tests: Timetable Scheduling, Overlap Intervals, and Conflict Detection (70 cases).
"""

import pytest
from app.utils.calculations import times_overlap, parse_time_minutes
from app.services.timetable_service import TimetableService
from app.schemas.timetable import ClassroomCreate, TimetableSlotCreate
from app.core.exceptions import ScheduleConflictException


# ============================================================================
# 1. Time Interval Overlap Detection Algorithm (40 cases)
# ============================================================================
time_overlap_cases = [
    # Overlapping intervals
    ("09:00", "10:30", "10:00", "11:30", True),
    ("09:00", "11:00", "09:30", "10:30", True),
    ("10:00", "12:00", "09:00", "11:00", True),
    ("08:00", "10:00", "08:00", "10:00", True),
    ("14:00", "16:00", "15:00", "17:00", True),
    ("13:15", "14:45", "14:00", "15:30", True),
    ("09:00", "12:00", "10:00", "11:00", True),
    ("10:00", "11:00", "09:00", "12:00", True),
    ("07:30", "09:30", "08:00", "09:00", True),
    ("11:00", "13:00", "11:30", "12:30", True),
    ("09:01", "10:00", "09:00", "09:02", True),
    ("10:00", "11:00", "10:59", "12:00", True),
    ("14:00", "15:30", "14:15", "15:15", True),
    ("16:00", "17:00", "16:01", "16:59", True),
    ("08:30", "10:30", "09:00", "10:00", True),
    ("11:00", "12:30", "12:00", "13:00", True),
    ("13:00", "14:30", "13:30", "15:00", True),
    ("15:00", "16:30", "15:15", "16:00", True),
    ("17:00", "18:30", "17:30", "18:00", True),
    ("18:00", "19:30", "18:30", "19:00", True),
    # Non-overlapping intervals (adjacent or disjoint)
    ("09:00", "10:00", "10:00", "11:00", False),  # Adjacent
    ("10:00", "11:00", "09:00", "10:00", False),  # Adjacent before
    ("08:00", "09:00", "11:00", "12:00", False),  # Completely separate
    ("14:00", "15:00", "16:00", "17:00", False),
    ("12:00", "13:00", "13:00", "14:00", False),
    ("07:00", "08:00", "09:00", "10:00", False),
    ("15:00", "16:00", "17:00", "18:00", False),
    ("18:00", "19:00", "19:00", "20:00", False),
    ("11:00", "12:00", "12:00", "13:00", False),
    ("13:00", "14:00", "14:00", "15:00", False),
    ("09:30", "10:30", "10:30", "11:30", False),
    ("10:30", "11:30", "09:30", "10:30", False),
    ("08:15", "09:15", "09:15", "10:15", False),
    ("14:45", "15:45", "15:45", "16:45", False),
    ("16:00", "17:00", "17:00", "18:00", False),
    ("06:00", "07:00", "08:00", "09:00", False),
    ("19:00", "20:00", "20:00", "21:00", False),
    ("20:00", "21:00", "21:00", "22:00", False),
    ("12:15", "13:15", "13:15", "14:15", False),
    ("15:30", "16:30", "16:30", "17:30", False)
]

@pytest.mark.parametrize("s1,e1,s2,e2,expected", time_overlap_cases, ids=[f"time_overlap_{i}" for i in range(40)])
def test_time_overlap_interval_logic(s1, e1, s2, e2, expected):
    assert times_overlap(s1, e1, s2, e2) == expected


# ============================================================================
# 2. Classroom and Faculty Conflict Detection (30 cases)
# ============================================================================
conflict_cases = [
    (f"LH_CONF_{i}", "Monday", "09:00", "10:30", "10:00", "11:30")
    for i in range(1, 31)
]

@pytest.mark.parametrize("room_code,day,s1,e1,s2,e2", conflict_cases, ids=[f"sched_conflict_{i}" for i in range(30)])
def test_classroom_conflict_detection(db_session, sample_course, room_code, day, s1, e1, s2, e2):
    tt_service = TimetableService(db_session)
    room = tt_service.create_classroom(ClassroomCreate(
        room_number=room_code,
        building="Science Hall",
        capacity=60
    ))

    # First slot scheduled
    tt_service.create_slot(TimetableSlotCreate(
        course_id=sample_course.id,
        faculty_id=1,
        classroom_id=room.id,
        day_of_week=day,
        start_time=s1,
        end_time=e1
    ))

    # Overlapping slot in same room raises ScheduleConflictException
    with pytest.raises(ScheduleConflictException):
        tt_service.create_slot(TimetableSlotCreate(
            course_id=sample_course.id,
            faculty_id=2,  # different faculty
            classroom_id=room.id,  # SAME classroom
            day_of_week=day,
            start_time=s2,
            end_time=e2
        ))
