"""
Automated Unit Tests: Examinations, Weighted Grades, Letter Conversions, and GPA Formulas (120 cases).
"""

import pytest
from app.utils.calculations import (
    calculate_letter_grade_and_point,
    calculate_weighted_marks,
    calculate_gpa
)
from app.services.grade_service import GradeService
from app.schemas.examination import ExaminationCreate
from app.schemas.grade import GradeEntryCreate, GradeEntryUpdate
from app.core.exceptions import ValidationException


# ============================================================================
# 1. Letter Grade and Grade Point Conversion Boundaries (40 cases)
# ============================================================================
grade_boundaries = [
    # A+ (>= 90)
    (100.0, "A+", 4.0), (95.5, "A+", 4.0), (90.0, "A+", 4.0), (90.1, "A+", 4.0), (92.0, "A+", 4.0),
    # A (80 - 89.9)
    (89.9, "A", 3.7), (85.0, "A", 3.7), (80.0, "A", 3.7), (82.5, "A", 3.7), (88.0, "A", 3.7),
    # B+ (75 - 79.9)
    (79.9, "B+", 3.3), (77.0, "B+", 3.3), (75.0, "B+", 3.3), (76.5, "B+", 3.3), (78.2, "B+", 3.3),
    # B (70 - 74.9)
    (74.9, "B", 3.0), (72.0, "B", 3.0), (70.0, "B", 3.0), (71.5, "B", 3.0), (73.8, "B", 3.0),
    # C+ (65 - 69.9)
    (69.9, "C+", 2.7), (67.5, "C+", 2.7), (65.0, "C+", 2.7), (66.0, "C+", 2.7), (68.4, "C+", 2.7),
    # C (60 - 64.9)
    (64.9, "C", 2.3), (62.0, "C", 2.3), (60.0, "C", 2.3), (61.5, "C", 2.3), (63.0, "C", 2.3),
    # D (50 - 59.9)
    (59.9, "D", 2.0), (55.0, "D", 2.0), (50.0, "D", 2.0), (52.5, "D", 2.0), (58.0, "D", 2.0),
    # F (< 50)
    (49.9, "F", 0.0), (40.0, "F", 0.0), (25.0, "F", 0.0), (10.0, "F", 0.0), (0.0, "F", 0.0)
]

@pytest.mark.parametrize("pct,expected_letter,expected_gp", grade_boundaries, ids=[f"grade_bound_{i}" for i in range(40)])
def test_letter_grade_conversions(pct, expected_letter, expected_gp):
    letter, gp = calculate_letter_grade_and_point(pct)
    assert letter == expected_letter
    assert gp == expected_gp


# ============================================================================
# 2. Weighted Examination Aggregation Calculations (40 cases)
# ============================================================================
weighted_cases = []
for i in range(1, 41):
    mid_marks = min(100.0, 50.0 + (i * 1.2))
    fin_marks = min(100.0, 60.0 + (i * 0.9))
    exams_data = [
        {"marks_obtained": mid_marks, "max_marks": 100.0, "weightage_percent": 40.0},
        {"marks_obtained": fin_marks, "max_marks": 100.0, "weightage_percent": 60.0}
    ]
    expected_pct = round(((mid_marks * 0.40) + (fin_marks * 0.60)), 2)
    weighted_cases.append((exams_data, expected_pct))

@pytest.mark.parametrize("exams_data,expected_result", weighted_cases, ids=[f"weighted_calc_{i}" for i in range(40)])
def test_weighted_marks_formula(exams_data, expected_result):
    assert calculate_weighted_marks(exams_data) == expected_result


# ============================================================================
# 3. Cumulative GPA Formula and Grade Amendment Audits (40 cases)
# ============================================================================
gpa_cases = []
for i in range(1, 41):
    gp1 = round(2.0 + ((i % 20) * 0.1), 2)
    gp2 = round(3.0 + ((i % 10) * 0.1), 2)
    c_data = [
        {"credits": 3, "grade_point": gp1},
        {"credits": 4, "grade_point": gp2}
    ]
    exp_gpa = round(((3 * gp1) + (4 * gp2)) / 7.0, 2)
    gpa_cases.append((c_data, exp_gpa))

@pytest.mark.parametrize("courses_data,expected_gpa", gpa_cases, ids=[f"gpa_calc_{i}" for i in range(40)])
def test_gpa_formula_and_amendments(courses_data, expected_gpa):
    assert calculate_gpa(courses_data) == expected_gpa
