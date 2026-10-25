"""
Academic Management Service: Departments, Faculty, and Courses.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.course import Course
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from app.schemas.course import CourseCreate, CourseUpdate
from app.core.exceptions import EntityNotFoundException, DuplicateEntityException


class AcademicService:
    def __init__(self, db: Session):
        self.db = db

    # Department operations
    def create_department(self, data: DepartmentCreate) -> Department:
        code_upper = data.code.strip().upper()
        if self.db.query(Department).filter(func.upper(Department.code) == code_upper).first():
            raise DuplicateEntityException("Department", "code", code_upper)
        if self.db.query(Department).filter(func.lower(Department.name) == data.name.strip().lower()).first():
            raise DuplicateEntityException("Department", "name", data.name)

        dept = Department(
            code=code_upper,
            name=data.name.strip(),
            head_of_department=data.head_of_department,
            building=data.building,
            budget=data.budget,
            is_active=data.is_active
        )
        self.db.add(dept)
        self.db.commit()
        self.db.refresh(dept)
        return dept

    def get_department(self, dept_id: int) -> Department:
        dept = self.db.query(Department).filter(Department.id == dept_id).first()
        if not dept:
            raise EntityNotFoundException("Department", dept_id)
        return dept

    def get_all_departments(self) -> List[Department]:
        return self.db.query(Department).all()

    def update_department(self, dept_id: int, data: DepartmentUpdate) -> Department:
        dept = self.get_department(dept_id)
        if data.name is not None:
            dept.name = data.name.strip()
        if data.head_of_department is not None:
            dept.head_of_department = data.head_of_department
        if data.building is not None:
            dept.building = data.building
        if data.budget is not None:
            dept.budget = data.budget
        if data.is_active is not None:
            dept.is_active = data.is_active
        self.db.commit()
        self.db.refresh(dept)
        return dept

    # Faculty operations
    def create_faculty(self, data: FacultyCreate) -> Faculty:
        emp_id = data.employee_id.strip().upper()
        if self.db.query(Faculty).filter(func.upper(Faculty.employee_id) == emp_id).first():
            raise DuplicateEntityException("Faculty", "employee_id", emp_id)
        if self.db.query(Faculty).filter(func.lower(Faculty.email) == data.email.strip().lower()).first():
            raise DuplicateEntityException("Faculty", "email", data.email)

        # Ensure department exists
        self.get_department(data.department_id)

        fac = Faculty(
            employee_id=emp_id,
            full_name=data.full_name.strip(),
            email=data.email.strip().lower(),
            phone_number=data.phone_number,
            department_id=data.department_id,
            designation=data.designation,
            specialization=data.specialization,
            is_active=data.is_active
        )
        self.db.add(fac)
        self.db.commit()
        self.db.refresh(fac)
        return fac

    def get_faculty(self, fac_id: int) -> Faculty:
        fac = self.db.query(Faculty).filter(Faculty.id == fac_id).first()
        if not fac:
            raise EntityNotFoundException("Faculty", fac_id)
        return fac

    def get_all_faculty(self) -> List[Faculty]:
        return self.db.query(Faculty).all()

    def update_faculty(self, fac_id: int, data: FacultyUpdate) -> Faculty:
        fac = self.get_faculty(fac_id)
        if data.full_name is not None:
            fac.full_name = data.full_name.strip()
        if data.email is not None:
            fac.email = data.email.strip().lower()
        if data.phone_number is not None:
            fac.phone_number = data.phone_number
        if data.department_id is not None:
            self.get_department(data.department_id)
            fac.department_id = data.department_id
        if data.designation is not None:
            fac.designation = data.designation
        if data.specialization is not None:
            fac.specialization = data.specialization
        if data.is_active is not None:
            fac.is_active = data.is_active
        self.db.commit()
        self.db.refresh(fac)
        return fac

    # Course operations
    def create_course(self, data: CourseCreate) -> Course:
        code_upper = data.code.strip().upper()
        if self.db.query(Course).filter(func.upper(Course.code) == code_upper).first():
            raise DuplicateEntityException("Course", "code", code_upper)

        self.get_department(data.department_id)
        if data.prerequisite_id:
            self.get_course(data.prerequisite_id)

        course = Course(
            code=code_upper,
            title=data.title.strip(),
            description=data.description,
            credits=data.credits,
            department_id=data.department_id,
            prerequisite_id=data.prerequisite_id,
            max_capacity=data.max_capacity,
            semester=data.semester,
            academic_year=data.academic_year,
            is_active=data.is_active
        )
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course

    def get_course(self, course_id: int) -> Course:
        c = self.db.query(Course).filter(Course.id == course_id).first()
        if not c:
            raise EntityNotFoundException("Course", course_id)
        return c

    def get_course_by_code(self, code: str) -> Course:
        c = self.db.query(Course).filter(func.upper(Course.code) == code.strip().upper()).first()
        if not c:
            raise EntityNotFoundException("Course", code)
        return c

    def get_all_courses(self) -> List[Course]:
        return self.db.query(Course).all()

    def update_course(self, course_id: int, data: CourseUpdate) -> Course:
        course = self.get_course(course_id)
        if data.title is not None:
            course.title = data.title.strip()
        if data.description is not None:
            course.description = data.description
        if data.credits is not None:
            course.credits = data.credits
        if data.department_id is not None:
            self.get_department(data.department_id)
            course.department_id = data.department_id
        if data.prerequisite_id is not None:
            self.get_course(data.prerequisite_id)
            course.prerequisite_id = data.prerequisite_id
        if data.max_capacity is not None:
            course.max_capacity = data.max_capacity
        if data.semester is not None:
            course.semester = data.semester
        if data.academic_year is not None:
            course.academic_year = data.academic_year
        if data.is_active is not None:
            course.is_active = data.is_active
        self.db.commit()
        self.db.refresh(course)
        return course
