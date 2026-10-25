"""
Safe CSV Export service for students, fees, attendance, and grades.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.student import Student
from app.models.fee import FeeInvoice, FeePayment
from app.models.attendance import AttendanceRecord
from app.models.grade import GradeEntry
from app.utils.csv_export import generate_safe_csv


class ExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_students_csv(self, department: Optional[str] = None) -> str:
        q = self.db.query(Student)
        if department:
            q = q.filter(Student.department == department)
        students = q.all()

        fields = [
            "id", "register_number", "full_name", "email", "phone_number",
            "department", "academic_year", "semester", "status", "gpa"
        ]
        rows = []
        for s in students:
            rows.append({
                "id": s.id,
                "register_number": s.register_number,
                "full_name": s.full_name,
                "email": s.email,
                "phone_number": s.phone_number,
                "department": s.department,
                "academic_year": s.academic_year,
                "semester": s.semester,
                "status": s.status,
                "gpa": s.gpa
            })

        return generate_safe_csv(fields, rows)

    def export_fees_csv(self) -> str:
        invoices = self.db.query(FeeInvoice).all()
        fields = [
            "invoice_number", "student_id", "title", "amount",
            "waiver_amount", "due_date", "status"
        ]
        rows = [
            {
                "invoice_number": inv.invoice_number,
                "student_id": inv.student_id,
                "title": inv.title,
                "amount": inv.amount,
                "waiver_amount": inv.waiver_amount,
                "due_date": inv.due_date,
                "status": inv.status
            }
            for inv in invoices
        ]
        return generate_safe_csv(fields, rows)
