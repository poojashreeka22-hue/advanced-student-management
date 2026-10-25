"""
Student Domain Service: Admissions, Record Management, Dossier Aggregation.
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.student_repo import StudentRepository
from app.repositories.audit_repo import AuditRepository
from app.repositories.attendance_repo import AttendanceRepository
from app.repositories.enrollment_repo import EnrollmentRepository
from app.repositories.fee_repo import FeeRepository
from app.models.student import Student
from app.models.enrollment import Enrollment
from app.models.fee import FeeInvoice
from app.schemas.student import StudentCreate, StudentUpdate
from app.core.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    ValidationException
)
from app.utils.validators import normalize_register_number
from app.utils.calculations import calculate_attendance_percentage


class StudentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = StudentRepository(db)
        self.audit_repo = AuditRepository(db)
        self.attendance_repo = AttendanceRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
        self.fee_repo = FeeRepository(db)

    def create_student(self, data: StudentCreate, current_username: Optional[str] = None) -> Student:
        norm_reg = normalize_register_number(data.register_number)

        # Check duplicate register number
        if self.repo.get_by_register_number(norm_reg):
            raise DuplicateEntityException("Student", "register_number", norm_reg)

        # Check duplicate email
        if self.repo.get_by_email(data.email):
            raise DuplicateEntityException("Student", "email", data.email)

        # Check identity duplicate if first/last/dob provided
        if data.first_name and data.last_name and data.date_of_birth:
            if self.repo.find_duplicate(data.first_name, data.last_name, data.date_of_birth):
                raise DuplicateEntityException(
                    "Student",
                    "identity",
                    f"{data.first_name} {data.last_name} born {data.date_of_birth}"
                )

        student = Student(
            register_number=norm_reg,
            first_name=data.first_name,
            last_name=data.last_name,
            full_name=data.full_name.strip(),
            email=data.email.strip().lower(),
            phone_number=data.phone_number.strip(),
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            department=data.department.strip(),
            department_id=data.department_id,
            academic_year=data.academic_year.strip(),
            semester=data.semester,
            status=data.status.lower() if data.status else "active",
            admission_date=data.admission_date,
            address=data.address,
            guardian_name=data.guardian_name,
            guardian_phone=data.guardian_phone,
            gpa=data.gpa
        )
        created = self.repo.create(student)
        self.audit_repo.log_event(
            action="CREATE",
            entity_type="Student",
            entity_id=str(created.id),
            username=current_username,
            new_values=f"Name: {created.full_name}, Reg: {created.register_number}"
        )
        return created

    def get_student(self, student_id: int) -> Student:
        student = self.repo.get(student_id)
        if not student:
            raise EntityNotFoundException("Student", student_id)
        return student

    def get_student_by_register_number(self, reg_num: str) -> Student:
        student = self.repo.get_by_register_number(reg_num)
        if not student:
            raise EntityNotFoundException("Student", reg_num)
        return student

    def update_student(
        self,
        student_id: int,
        data: StudentUpdate,
        current_username: Optional[str] = None
    ) -> Student:
        student = self.get_student(student_id)
        old_val = f"Name: {student.full_name}, Reg: {student.register_number}, Dept: {student.department}"

        # If register number changed, check uniqueness
        if data.register_number is not None:
            norm_reg = normalize_register_number(data.register_number)
            if norm_reg != student.register_number:
                existing = self.repo.get_by_register_number(norm_reg)
                if existing and existing.id != student.id:
                    raise DuplicateEntityException("Student", "register_number", norm_reg)
                student.register_number = norm_reg

        # If email changed, check uniqueness
        if data.email is not None:
            cleaned_email = data.email.strip().lower()
            if cleaned_email != student.email.lower():
                existing = self.repo.get_by_email(cleaned_email)
                if existing and existing.id != student.id:
                    raise DuplicateEntityException("Student", "email", cleaned_email)
                student.email = cleaned_email

        # Update other fields if provided
        for field in [
            "full_name", "first_name", "last_name", "phone_number",
            "date_of_birth", "gender", "department", "department_id",
            "academic_year", "semester", "status", "admission_date",
            "address", "guardian_name", "guardian_phone", "gpa"
        ]:
            val = getattr(data, field, None)
            if val is not None:
                setattr(student, field, val)

        updated = self.repo.update(student)
        self.audit_repo.log_event(
            action="UPDATE",
            entity_type="Student",
            entity_id=str(updated.id),
            username=current_username,
            old_values=old_val,
            new_values=f"Name: {updated.full_name}, Reg: {updated.register_number}, Dept: {updated.department}"
        )
        return updated

    def update_status(
        self,
        student_id: int,
        new_status: str,
        reason: Optional[str] = None,
        current_username: Optional[str] = None
    ) -> Student:
        allowed = {"applicant", "active", "suspended", "graduated", "withdrawn"}
        normalized = new_status.strip().lower()
        if normalized not in allowed:
            raise ValidationException(f"Invalid status '{new_status}'. Must be one of {allowed}")

        student = self.get_student(student_id)
        old_status = student.status
        student.status = normalized
        updated = self.repo.update(student)

        self.audit_repo.log_event(
            action="STATUS_CHANGE",
            entity_type="Student",
            entity_id=str(student_id),
            username=current_username,
            old_values=f"Status: {old_status}",
            new_values=f"Status: {normalized}, Reason: {reason or 'N/A'}"
        )
        return updated

    def delete_student(self, student_id: int, current_username: Optional[str] = None) -> None:
        student = self.get_student(student_id)

        # Safeguard: Prevent deleting student with active enrollments
        enr_count = self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.status == "enrolled"
        ).count()
        if enr_count > 0:
            raise ValidationException(
                f"Cannot delete student '{student.full_name}' ({student.register_number}). "
                f"Student has {enr_count} active course enrollment(s). Withdraw or drop them first."
            )

        # Safeguard: Prevent deleting student with outstanding fee invoices
        unpaid_invoices = self.db.query(FeeInvoice).filter(
            FeeInvoice.student_id == student_id,
            FeeInvoice.status.in_(["pending", "partial", "overdue"])
        ).count()
        if unpaid_invoices > 0:
            raise ValidationException(
                f"Cannot delete student '{student.full_name}' ({student.register_number}). "
                f"Student has {unpaid_invoices} outstanding/unpaid fee invoice(s). Settle financial ledger first."
            )

        reg = student.register_number
        name = student.full_name
        self.repo.delete(student)
        self.audit_repo.log_event(
            action="DELETE",
            entity_type="Student",
            entity_id=str(student_id),
            username=current_username,
            old_values=f"Deleted student {name} ({reg})"
        )

    def search_students(
        self,
        search: Optional[str] = None,
        department: Optional[str] = None,
        academic_year: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "id",
        sort_desc: bool = False
    ) -> Tuple[List[Student], int]:
        return self.repo.search_and_filter(
            search=search,
            department=department,
            academic_year=academic_year,
            status=status,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_desc=sort_desc
        )

    def get_student_dossier(self, student_id: int) -> Dict[str, Any]:
        student = self.get_student(student_id)

        # Enrollments
        enrollments = self.enrollment_repo.get_by_student(student_id)

        # Attendance calculation
        attendance_records = self.attendance_repo.get_student_all_records(student_id)
        records_dict = [
            {"status": r.status, "is_cancelled": r.is_cancelled}
            for r in attendance_records
        ]
        attendance_stats = calculate_attendance_percentage(records_dict)

        # Fee calculations
        invoices = self.fee_repo.get_student_invoices(student_id)
        total_balance = 0.0
        for inv in invoices:
            payments = self.fee_repo.get_payments_for_invoice(inv.id)
            paid = sum(p.amount_paid for p in payments)
            net_inv = max(0.0, inv.amount - inv.waiver_amount)
            total_balance += max(0.0, net_inv - paid)

        return {
            "student": student,
            "total_enrollments": len(enrollments),
            "attendance_rate": attendance_stats["attendance_percentage"],
            "outstanding_fee_balance": round(total_balance, 2)
        }
