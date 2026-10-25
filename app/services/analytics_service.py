"""
Analytics and Reporting Service for University Dashboard.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.student import Student
from app.models.course import Course
from app.models.faculty import Faculty
from app.models.department import Department
from app.models.attendance import AttendanceRecord
from app.models.fee import FeeInvoice, FeePayment
from app.models.grade import GradeEntry
from app.schemas.analytics import StatsResponse, DashboardMetrics, GradeDistributionItem, DepartmentPerformance
from app.utils.calculations import calculate_attendance_percentage


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_legacy_stats(self) -> StatsResponse:
        """Returns the legacy stats format for full backward compatibility."""
        total = self.db.query(Student).count()

        # Department counts
        dept_rows = self.db.query(Student.department, func.count(Student.id)).group_by(Student.department).all()
        department_counts = {row[0]: row[1] for row in dept_rows if row[0]}

        # Academic year counts
        year_rows = self.db.query(Student.academic_year, func.count(Student.id)).group_by(Student.academic_year).all()
        academic_year_counts = {row[0]: row[1] for row in year_rows if row[0]}

        return StatsResponse(
            total_students=total,
            department_counts=department_counts,
            academic_year_counts=academic_year_counts
        )

    def get_dashboard_metrics(self) -> DashboardMetrics:
        total_students = self.db.query(Student).count()
        active_students = self.db.query(Student).filter(Student.status == "active").count()
        total_courses = self.db.query(Course).count()
        total_faculty = self.db.query(Faculty).count()

        # Overall attendance
        attendance_records = self.db.query(AttendanceRecord).all()
        records_dict = [{"status": r.status, "is_cancelled": r.is_cancelled} for r in attendance_records]
        att_calc = calculate_attendance_percentage(records_dict)
        overall_attendance_rate = att_calc["attendance_percentage"]

        # Fees
        invoices = self.db.query(FeeInvoice).all()
        payments = self.db.query(FeePayment).all()
        total_fees_collected = sum(p.amount_paid for p in payments)

        total_invoiced_net = sum(max(0.0, inv.amount - inv.waiver_amount) for inv in invoices)
        total_fees_outstanding = max(0.0, total_invoiced_net - total_fees_collected)

        # Distributions
        dept_rows = self.db.query(Student.department, func.count(Student.id)).group_by(Student.department).all()
        department_distribution = {row[0]: row[1] for row in dept_rows if row[0]}

        year_rows = self.db.query(Student.academic_year, func.count(Student.id)).group_by(Student.academic_year).all()
        academic_year_distribution = {row[0]: row[1] for row in year_rows if row[0]}

        status_rows = self.db.query(Student.status, func.count(Student.id)).group_by(Student.status).all()
        status_distribution = {row[0]: row[1] for row in status_rows if row[0]}

        return DashboardMetrics(
            total_students=total_students,
            active_students=active_students,
            total_courses=total_courses,
            total_faculty=total_faculty,
            overall_attendance_rate=overall_attendance_rate,
            total_fees_collected=round(total_fees_collected, 2),
            total_fees_outstanding=round(total_fees_outstanding, 2),
            department_distribution=department_distribution,
            academic_year_distribution=academic_year_distribution,
            status_distribution=status_distribution,
            recent_admissions_count=total_students
        )

    def get_grade_distribution(self) -> List[GradeDistributionItem]:
        grades = self.db.query(GradeEntry).all()
        total = len(grades)
        if total == 0:
            return []

        counts: Dict[str, int] = {}
        for g in grades:
            let = g.letter_grade or "N/A"
            counts[let] = counts.get(let, 0) + 1

        return [
            GradeDistributionItem(
                letter_grade=k,
                count=v,
                percentage=round((v / total) * 100.0, 1)
            )
            for k, v in sorted(counts.items())
        ]

    def get_department_performance(self) -> List[DepartmentPerformance]:
        departments = self.db.query(Department).all()
        results = []

        for d in departments:
            students = self.db.query(Student).filter(
                (Student.department == d.name) | (Student.department_id == d.id)
            ).all()
            st_count = len(students)
            avg_gpa = round(sum(s.gpa for s in students) / st_count, 2) if st_count > 0 else 0.0

            # Department attendance
            st_ids = [s.id for s in students]
            att_records = self.db.query(AttendanceRecord).filter(AttendanceRecord.student_id.in_(st_ids)).all() if st_ids else []
            calc = calculate_attendance_percentage([{"status": r.status, "is_cancelled": r.is_cancelled} for r in att_records])

            results.append(
                DepartmentPerformance(
                    department=d.name,
                    student_count=st_count,
                    average_gpa=avg_gpa,
                    attendance_rate=calc["attendance_percentage"]
                )
            )
        return results
