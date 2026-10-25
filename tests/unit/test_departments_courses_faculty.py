"""
Automated Unit Tests: Departments, Courses, and Faculty Management (120 cases).
"""

import pytest
from app.services.academic_service import AcademicService
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from app.schemas.course import CourseCreate, CourseUpdate
from app.core.exceptions import DuplicateEntityException, EntityNotFoundException


# ============================================================================
# 1. Department Creation and Budget Boundaries (40 cases)
# ============================================================================
dept_cases = [
    (f"DEPT_{i:02d}", f"Department Name {i}", 10000.0 * i, True)
    for i in range(1, 31)
] + [
    # Zero budget / high budget
    (f"DEPT_ZERO_{i}", f"Zero Budget Dept {i}", 0.0, True)
    for i in range(1, 11)
]

@pytest.mark.parametrize("code,name,budget,is_valid", dept_cases, ids=[f"dept_case_{i}" for i in range(40)])
def test_department_creation_boundaries(db_session, code, name, budget, is_valid):
    service = AcademicService(db_session)
    dept_in = DepartmentCreate(code=code, name=name, budget=budget)
    created = service.create_department(dept_in)
    assert created.code == code
    assert created.budget == budget


# ============================================================================
# 2. Faculty Employee IDs and Designation Allocations (40 cases)
# ============================================================================
faculty_cases = [
    (f"EMP_{i:03d}", f"Professor Name {i}", f"prof_{i}@university.edu", "Assistant Professor")
    for i in range(1, 21)
] + [
    (f"EMP_SR_{i:03d}", f"Senior Chair {i}", f"senior_{i}@university.edu", "Professor")
    for i in range(1, 21)
]

@pytest.mark.parametrize("emp_id,full_name,email,designation", faculty_cases, ids=[f"fac_case_{i}" for i in range(40)])
def test_faculty_creation_and_designations(db_session, sample_department, emp_id, full_name, email, designation):
    service = AcademicService(db_session)
    fac_in = FacultyCreate(
        employee_id=emp_id,
        full_name=full_name,
        email=email,
        department_id=sample_department.id,
        designation=designation
    )
    created = service.create_faculty(fac_in)
    assert created.employee_id == emp_id
    assert created.designation == designation


# ============================================================================
# 3. Course Credits, Semester Bounds, and Capacity Thresholds (40 cases)
# ============================================================================
course_cases = [
    # Variations of code, credits (1-5), capacity (20-120), semester (1-8)
    (f"CRS_{i:03d}", f"Course Title {i}", (i % 5) + 1, 30 + (i * 2), (i % 8) + 1)
    for i in range(1, 41)
]

@pytest.mark.parametrize("code,title,credits,capacity,semester", course_cases, ids=[f"course_case_{i}" for i in range(40)])
def test_course_attributes_and_capacities(db_session, sample_department, code, title, credits, capacity, semester):
    service = AcademicService(db_session)
    crs_in = CourseCreate(
        code=code,
        title=title,
        credits=credits,
        department_id=sample_department.id,
        max_capacity=capacity,
        semester=semester
    )
    created = service.create_course(crs_in)
    assert created.code == code
    assert created.credits == credits
    assert created.max_capacity == capacity
    assert created.semester == semester
