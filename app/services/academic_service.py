"""
Academic Management Service: Departments, Faculty, and Courses.
Enforces real university workflows, HOD governance, prerequisite cycles, and deletion safeguards.
"""

from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.course import Course
from app.models.student import Student
from app.models.enrollment import Enrollment
from app.models.examination import Examination
from app.models.timetable import TimetableSlot
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from app.schemas.course import CourseCreate, CourseUpdate
from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    ValidationException
)


class AcademicService:
    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # Department Operations & HOD Governance
    # =========================================================================
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
            hod_faculty_id=data.hod_faculty_id,
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
        if data.name is not None and data.name.strip().lower() != dept.name.lower():
            existing = self.db.query(Department).filter(
                func.lower(Department.name) == data.name.strip().lower(),
                Department.id != dept_id
            ).first()
            if existing:
                raise DuplicateEntityException("Department", "name", data.name)
            dept.name = data.name.strip()

        if data.head_of_department is not None:
            dept.head_of_department = data.head_of_department
        if data.building is not None:
            dept.building = data.building
        if data.budget is not None:
            dept.budget = data.budget
        if data.is_active is not None:
            dept.is_active = data.is_active
        if data.hod_faculty_id is not None:
            # Route through assign_hod to ensure all rules are honored
            return self.assign_hod(dept_id, data.hod_faculty_id)

        self.db.commit()
        self.db.refresh(dept)
        return dept

    def assign_hod(self, department_id: int, faculty_id: int) -> Department:
        """
        Assign an active faculty member as Head of Department (HOD).
        Rules enforced:
        1. Department must exist and be active.
        2. Faculty member must exist and be active (not terminated/inactive).
        3. Faculty member must belong to the department they are assigned to lead.
        4. Faculty member cannot already be serving as HOD of another department.
        5. Exactly one active HOD per department.
        """
        dept = self.get_department(department_id)
        if not dept.is_active:
            raise ValidationException(f"Cannot assign HOD to inactive department '{dept.name}'.")

        fac = self.get_faculty(faculty_id)
        if not fac.is_active:
            raise ValidationException(
                f"Cannot assign faculty member '{fac.full_name}' as HOD because their status is inactive or terminated."
            )

        if fac.department_id != department_id:
            raise ValidationException(
                f"Cannot assign faculty member '{fac.full_name}' as HOD of '{dept.name}'. "
                f"Faculty belongs to department #{fac.department_id}, not department #{department_id}."
            )

        # Check if faculty member is already HOD of another department
        other_dept = self.db.query(Department).filter(
            Department.hod_faculty_id == faculty_id,
            Department.id != department_id
        ).first()
        if other_dept:
            raise ValidationException(
                f"Faculty member '{fac.full_name}' is already serving as Head of Department for '{other_dept.name}'. "
                f"A faculty member cannot lead multiple departments simultaneously."
            )

        dept.hod_faculty_id = fac.id
        dept.head_of_department = fac.full_name
        self.db.commit()
        self.db.refresh(dept)
        return dept

    def vacate_hod(self, department_id: int) -> Department:
        """Vacate the Head of Department role for a department."""
        dept = self.get_department(department_id)
        dept.hod_faculty_id = None
        dept.head_of_department = None
        self.db.commit()
        self.db.refresh(dept)
        return dept

    def delete_department(self, dept_id: int) -> None:
        """
        Safely delete a department only when no dependent records exist.
        Blocks deletion if active faculty, courses, or students are associated.
        """
        dept = self.get_department(dept_id)

        # Check associated faculty
        fac_count = self.db.query(Faculty).filter(Faculty.department_id == dept_id).count()
        if fac_count > 0:
            raise ValidationException(
                f"Cannot delete department '{dept.name}'. It contains {fac_count} associated faculty member(s). "
                f"Reassign or archive them first."
            )

        # Check associated courses
        course_count = self.db.query(Course).filter(Course.department_id == dept_id).count()
        if course_count > 0:
            raise ValidationException(
                f"Cannot delete department '{dept.name}'. It contains {course_count} course(s). "
                f"Reassign or delete the courses first."
            )

        # Check enrolled students
        student_count = self.db.query(Student).filter(
            (Student.department_id == dept_id) | (Student.department == dept.name)
        ).count()
        if student_count > 0:
            raise ValidationException(
                f"Cannot delete department '{dept.name}'. It has {student_count} registered student(s)."
            )

        self.db.delete(dept)
        self.db.commit()

    # =========================================================================
    # Faculty Operations & Reassignment/Transfer Safeguards
    # =========================================================================
    def create_faculty(self, data: FacultyCreate) -> Faculty:
        emp_id = data.employee_id.strip().upper()
        if self.db.query(Faculty).filter(func.upper(Faculty.employee_id) == emp_id).first():
            raise DuplicateEntityException("Faculty", "employee_id", emp_id)
        if self.db.query(Faculty).filter(func.lower(Faculty.email) == data.email.strip().lower()).first():
            raise DuplicateEntityException("Faculty", "email", data.email)

        # Ensure department exists and is active
        dept = self.get_department(data.department_id)
        if not dept.is_active:
            raise ValidationException(f"Cannot assign faculty to inactive department '{dept.name}'.")

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

        # Prevent deactivating faculty if they are currently an active HOD
        if data.is_active is False and fac.is_active:
            leading_dept = self.db.query(Department).filter(Department.hod_faculty_id == fac_id).first()
            if leading_dept:
                raise ValidationException(
                    f"Cannot deactivate faculty member '{fac.full_name}' while they are serving as Head of Department for '{leading_dept.name}'. "
                    f"Vacate or reassign the HOD role first."
                )

        # Handle department transfer / reassignment
        if data.department_id is not None and data.department_id != fac.department_id:
            new_dept = self.get_department(data.department_id)
            if not new_dept.is_active:
                raise ValidationException(f"Cannot transfer faculty to inactive department '{new_dept.name}'.")

            # Resolve previous HOD assignment upon transfer: vacate old department HOD role
            old_dept = self.db.query(Department).filter(
                Department.id == fac.department_id,
                Department.hod_faculty_id == fac.id
            ).first()
            if old_dept:
                old_dept.hod_faculty_id = None
                old_dept.head_of_department = None

            fac.department_id = data.department_id

        if data.full_name is not None:
            fac.full_name = data.full_name.strip()
            # Sync HOD name if faculty is leading a department
            hod_dept = self.db.query(Department).filter(Department.hod_faculty_id == fac.id).first()
            if hod_dept:
                hod_dept.head_of_department = fac.full_name

        if data.email is not None:
            new_email = data.email.strip().lower()
            if new_email != fac.email:
                existing = self.db.query(Faculty).filter(
                    func.lower(Faculty.email) == new_email,
                    Faculty.id != fac_id
                ).first()
                if existing:
                    raise DuplicateEntityException("Faculty", "email", new_email)
                fac.email = new_email

        if data.phone_number is not None:
            fac.phone_number = data.phone_number
        if data.designation is not None:
            fac.designation = data.designation
        if data.specialization is not None:
            fac.specialization = data.specialization
        if data.is_active is not None:
            fac.is_active = data.is_active

        self.db.commit()
        self.db.refresh(fac)
        return fac

    def delete_faculty(self, fac_id: int) -> None:
        """
        Safely delete a faculty member.
        Blocks deletion if serving as HOD or scheduled in active timetable slots.
        """
        fac = self.get_faculty(fac_id)

        # Check HOD position
        hod_dept = self.db.query(Department).filter(Department.hod_faculty_id == fac_id).first()
        if hod_dept:
            raise ValidationException(
                f"Cannot delete faculty member '{fac.full_name}'. They are currently serving as Head of Department for '{hod_dept.name}'. "
                f"Vacate or reassign the HOD role first."
            )

        # Check timetable scheduling
        slot_count = self.db.query(TimetableSlot).filter(TimetableSlot.faculty_id == fac_id).count()
        if slot_count > 0:
            raise ValidationException(
                f"Cannot delete faculty member '{fac.full_name}'. They are assigned to {slot_count} active timetable slot(s). "
                f"Reassign timetable duties first."
            )

        self.db.delete(fac)
        self.db.commit()

    # =========================================================================
    # Course Operations & Prerequisite Cycle Validation
    # =========================================================================
    def _check_circular_prerequisite(self, course_id: Optional[int], candidate_prereq_id: int) -> None:
        """
        Detect and reject self-prerequisites and circular prerequisite chains (e.g. A -> B -> A).
        """
        if course_id is not None and course_id == candidate_prereq_id:
            raise ValidationException("A course cannot have itself as a prerequisite.")

        visited: Set[int] = set()
        curr_id: Optional[int] = candidate_prereq_id

        while curr_id is not None:
            if course_id is not None and curr_id == course_id:
                raise ValidationException(
                    f"Circular prerequisite dependency detected: Course #{course_id} is already in the "
                    f"prerequisite dependency chain of Course #{candidate_prereq_id}."
                )
            if curr_id in visited:
                # Loop in existing chain detected
                break
            visited.add(curr_id)
            parent = self.db.query(Course).filter(Course.id == curr_id).first()
            if not parent:
                break
            curr_id = parent.prerequisite_id

    def create_course(self, data: CourseCreate) -> Course:
        code_upper = data.code.strip().upper()
        if self.db.query(Course).filter(func.upper(Course.code) == code_upper).first():
            raise DuplicateEntityException("Course", "code", code_upper)

        self.get_department(data.department_id)

        if data.prerequisite_id:
            prereq = self.get_course(data.prerequisite_id)
            if not prereq.is_active:
                raise ValidationException(f"Cannot set inactive course '{prereq.code}' as a prerequisite.")
            # Validate no cycle
            self._check_circular_prerequisite(None, data.prerequisite_id)

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
            if data.prerequisite_id == course_id:
                raise ValidationException("A course cannot have itself as a prerequisite.")
            prereq = self.get_course(data.prerequisite_id)
            if not prereq.is_active:
                raise ValidationException(f"Cannot set inactive course '{prereq.code}' as a prerequisite.")
            self._check_circular_prerequisite(course_id, data.prerequisite_id)
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

    def delete_course(self, course_id: int) -> None:
        """
        Safely delete a course only when no dependent prerequisites, enrollments, exams, or timetable slots exist.
        """
        course = self.get_course(course_id)

        # Check if prerequisite for another course
        dependent_courses = self.db.query(Course).filter(Course.prerequisite_id == course_id).all()
        if dependent_courses:
            dep_codes = ", ".join([c.code for c in dependent_courses])
            raise ValidationException(
                f"Cannot delete course '{course.code}'. It is a prerequisite for: {dep_codes}."
            )

        # Check student enrollments
        enr_count = self.db.query(Enrollment).filter(Enrollment.course_id == course_id).count()
        if enr_count > 0:
            raise ValidationException(
                f"Cannot delete course '{course.code}'. It has {enr_count} student enrollment record(s)."
            )

        # Check examinations
        exam_count = self.db.query(Examination).filter(Examination.course_id == course_id).count()
        if exam_count > 0:
            raise ValidationException(
                f"Cannot delete course '{course.code}'. It has {exam_count} scheduled examination(s)."
            )

        # Check timetable slots
        slot_count = self.db.query(TimetableSlot).filter(TimetableSlot.course_id == course_id).count()
        if slot_count > 0:
            raise ValidationException(
                f"Cannot delete course '{course.code}'. It has {slot_count} timetable slot(s) assigned."
            )

        self.db.delete(course)
        self.db.commit()
