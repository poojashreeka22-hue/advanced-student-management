"""
Interactive Demonstration Scenario Script.
Demonstrates the complete end-to-end academic lifecycle:
1. Registering a new student (Admissions)
2. Enrolling the student in an active course
3. Recording attendance sessions
4. Entering examination assessment marks
5. Generating an academic transcript and GPA calculation
6. Recording a simulated partial fee payment with balance tracking
7. Searching and exporting the student's record to CSV
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import SessionLocal
from app.services.student_service import StudentService
from app.services.enrollment_service import EnrollmentService
from app.services.academic_service import AcademicService
from app.services.attendance_service import AttendanceService
from app.services.grade_service import GradeService
from app.services.fee_service import FeeService
from app.services.export_service import ExportService
from app.schemas.student import StudentCreate
from app.schemas.enrollment import EnrollmentCreate
from app.schemas.attendance import AttendanceCreate
from app.schemas.examination import ExaminationCreate
from app.schemas.grade import GradeEntryCreate
from app.schemas.fee import FeeInvoiceCreate, FeePaymentCreate


def run_demo():
    db = SessionLocal()
    try:
        print("=" * 70)
        print("EDUTRACK ENTERPRISE — DEMONSTRATION SCENARIO")
        print("=" * 70)

        student_service = StudentService(db)
        academic_service = AcademicService(db)
        enrollment_service = EnrollmentService(db)
        attendance_service = AttendanceService(db)
        grade_service = GradeService(db)
        fee_service = FeeService(db)
        export_service = ExportService(db)

        # Step 1: Register New Student
        print("\n[STEP 1] Admitting New Student...")
        reg_no = "DEMO2026099"
        # Cleanup if demo was run before
        existing = student_service.repo.get_by_register_number(reg_no)
        if existing:
            student_service.delete_student(existing.id)

        student = student_service.create_student(StudentCreate(
            full_name="Jonathan Harker",
            register_number=reg_no,
            first_name="Jonathan",
            last_name="Harker",
            email="jonathan.harker@demo.edu",
            phone_number="9876543299",
            department="Computer Science",
            academic_year="1st Year",
            semester=1,
            status="active"
        ), current_username="admin")
        print(f" -> Student Admitted: {student.full_name} | Reg: {student.register_number} | ID: {student.id}")

        # Step 2: Enroll in Course
        print("\n[STEP 2] Enrolling in Course CS101...")
        course = academic_service.get_course_by_code("CS101")
        enrollment = enrollment_service.enroll_student(EnrollmentCreate(
            student_id=student.id,
            course_id=course.id,
            academic_year="2026-2027",
            semester=1
        ))
        print(f" -> Enrolled in: {course.code} ({course.title}) | Status: {enrollment.status}")

        # Step 3: Record Attendance
        print("\n[STEP 3] Recording Class Attendance...")
        for day in range(1, 5):
            date_str = f"2026-10-{10 + day}"
            att = attendance_service.record_attendance(AttendanceCreate(
                student_id=student.id,
                course_id=course.id,
                session_date=date_str,
                slot_number=1,
                status="present" if day != 3 else "late"
            ), recorded_by="Prof. Alan Turing")
            print(f" -> Date: {att.session_date} | Slot: {att.slot_number} | Status: {att.status}")

        att_summary = attendance_service.get_student_course_attendance(student.id, course.id)
        print(f" -> Course Attendance Rate: {att_summary['attendance_percentage']}% (Shortage Warning: {att_summary['is_shortage']})")

        # Step 4: Schedule Exam and Enter Marks
        print("\n[STEP 4] Entering Examination Marks...")
        exams = grade_service.get_course_examinations(course.id)
        if not exams:
            exam = grade_service.create_examination(ExaminationCreate(
                course_id=course.id,
                title="Midterm Assessment",
                exam_type="midterm",
                max_marks=100.0,
                weightage_percent=100.0,
                semester=1
            ))
        else:
            exam = exams[0]

        grade = grade_service.enter_grade(GradeEntryCreate(
            examination_id=exam.id,
            student_id=student.id,
            marks_obtained=95.0,
            is_absent=False,
            remarks="Outstanding project submission"
        ), graded_by="Prof. Alan Turing")
        print(f" -> Exam: {exam.title} | Marks: {grade.marks_obtained}/{exam.max_marks} | Letter Grade: {grade.letter_grade}")

        # Step 5: Academic Transcript & GPA
        print("\n[STEP 5] Generating Official Transcript & GPA...")
        transcript = grade_service.generate_student_transcript(student.id)
        print(f" -> Student: {transcript.student_name} ({transcript.register_number})")
        print(f" -> Cumulative GPA: {transcript.gpa} / 4.00")
        for item in transcript.items:
            print(f"    * {item.course_code}: {item.course_title} ({item.credits} cr) - {item.letter_grade} ({item.grade_point} GP)")

        # Step 6: Fee Invoicing & Payment
        print("\n[STEP 6] Fee Ledger and Payment Transaction...")
        invoice = fee_service.create_invoice(FeeInvoiceCreate(
            student_id=student.id,
            title="Semester 1 Tuition & Tech Fee",
            amount=2500.0,
            waiver_amount=300.0,
            due_date="2026-11-30"
        ), created_by="Finance Bursar")
        print(f" -> Generated Invoice: {invoice.invoice_number} | Amount: ${invoice.amount} | Scholarship Waiver: ${invoice.waiver_amount}")
        print(f"    Net Payable: ${invoice.amount - invoice.waiver_amount}")

        payment = fee_service.record_payment(FeePaymentCreate(
            invoice_id=invoice.id,
            amount_paid=1200.0,
            payment_method="bank_transfer",
            notes="Initial installment"
        ), recorded_by="Finance Bursar")
        print(f" -> Payment Processed: ${payment.amount_paid} | Ref: {payment.payment_reference}")

        overview = fee_service.get_student_fee_overview(student.id)[0]
        print(f" -> Remaining Balance Due: ${overview['balance_due']} | Status: {overview['invoice'].status}")

        # Step 7: Search and CSV Export
        print("\n[STEP 7] Searching Student & Generating CSV Export...")
        search_results, count = student_service.search_students(search="Harker")
        print(f" -> Search query 'Harker' returned {count} record(s): {search_results[0].full_name}")

        csv_content = export_service.export_students_csv(department="Computer Science")
        print(f" -> CSV Export Generated ({len(csv_content)} bytes). Preview:")
        for line in csv_content.splitlines()[:3]:
            print(f"    {line}")

        print("\n" + "=" * 70)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY WITHOUT ERRORS.")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    run_demo()
