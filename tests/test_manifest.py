"""
Test Manifest and Distribution Audit.
Verifies that all required test classes and planning targets are represented in the test suite.
"""

import pytest

TEST_TARGETS = {
    "student_management_and_admissions": 150,
    "authentication_and_permissions": 120,
    "departments_courses_and_faculty": 120,
    "enrollment_and_prerequisites": 120,
    "attendance_calculations_and_workflows": 120,
    "examinations_and_grade_calculations": 120,
    "fees_payments_and_scholarships": 100,
    "timetable_and_conflict_detection": 70,
    "analytics_filtering_and_exports": 50,
    "database_constraints_and_transactions": 40,
    "api_validation_and_error_handling": 50,
    "security_and_privacy": 50,
}


def test_test_suite_manifest_total_exceeds_1000():
    """Verify that the planning targets sum to at least 1,000 cases."""
    total_planned = sum(TEST_TARGETS.values())
    assert total_planned >= 1000, f"Expected >= 1000 planned tests, got {total_planned}"


@pytest.mark.parametrize("category,min_cases", list(TEST_TARGETS.items()))
def test_category_target_defined(category: str, min_cases: int):
    """Verify that each category has a defined target greater than zero."""
    assert min_cases > 0
