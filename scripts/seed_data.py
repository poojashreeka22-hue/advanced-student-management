"""
Repeatable Synthetic Development Seed Script.
Populates realistic academic data: Departments, Faculty, Courses, Classrooms, Students, Enrollments, Attendance, Exams, Grades, and Fees.
Safe to run multiple times without creating duplicate records.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import SessionLocal
from app.database.init_db import init_db
from app.models import (
    User, Department, Faculty, Course, Classroom, Student,
    Enrollment, AttendanceRecord, Examination, GradeEntry,
    FeeInvoice, FeePayment, TimetableSlot
)
from app.core.security import hash_password
from app.core.logging import logger


def seed_database():
    init_db()
    db = SessionLocal()

    try:
        logger.info("Beginning repeatable synthetic seeding...")

        # 1. Departments
        departments_data = [
            {"code": "CS", "name": "Computer Science", "head_of_department": "Dr. Ada Lovelace", "building": "Turing Hall", "budget": 650000.0},
            {"code": "IT", "name": "Information Technology", "head_of_department": "Dr. Tim Berners-Lee", "building": "Shannon Wing", "budget": 520000.0},
            {"code": "ECE", "name": "Electronics & Communication", "head_of_department": "Dr. Claude Shannon", "building": "Maxwell Lab", "budget": 580000.0},
            {"code": "MECH", "name": "Mechanical Engineering", "head_of_department": "Dr. Nikola Tesla", "building": "Watt Pavilion", "budget": 610000.0},
            {"code": "CIVIL", "name": "Civil Engineering", "head_of_department": "Dr. John Smeaton", "building": "Brindley Block", "budget": 490000.0}
        ]
        dept_map = {}
        for d in departments_data:
            existing = db.query(Department).filter(Department.code == d["code"]).first()
            if not existing:
                existing = Department(**d)
                db.add(existing)
                db.commit()
                db.refresh(existing)
            dept_map[d["code"]] = existing

        # 2. Classrooms
        classrooms_data = [
            {"room_number": "LH-101", "building": "Turing Hall", "capacity": 80, "room_type": "lecture_hall"},
            {"room_number": "LAB-201", "building": "Shannon Wing", "capacity": 45, "room_type": "lab"},
            {"room_number": "SEM-301", "building": "Maxwell Lab", "capacity": 50, "room_type": "seminar"},
            {"room_number": "LH-102", "building": "Watt Pavilion", "capacity": 90, "room_type": "lecture_hall"}
        ]
        classroom_map = {}
        for cr in classrooms_data:
            existing = db.query(Classroom).filter(Classroom.room_number == cr["room_number"]).first()
            if not existing:
                existing = Classroom(**cr)
                db.add(existing)
                db.commit()
                db.refresh(existing)
            classroom_map[cr["room_number"]] = existing

        # 3. Faculty
        faculty_data = [
            {"employee_id": "FAC_CS_01", "full_name": "Prof. Alan Turing", "email": "alan.turing@university.edu", "department_id": dept_map["CS"].id, "designation": "Professor", "specialization": "Computation Theory"},
            {"employee_id": "FAC_CS_02", "full_name": "Dr. Grace Hopper", "email": "grace.hopper@university.edu", "department_id": dept_map["CS"].id, "designation": "Associate Professor", "specialization": "Compiler Design"},
            {"employee_id": "FAC_IT_01", "full_name": "Dr. Vint Cerf", "email": "vint.cerf@university.edu", "department_id": dept_map["IT"].id, "designation": "Professor", "specialization": "Computer Networks"},
            {"employee_id": "FAC_ECE_01", "full_name": "Dr. Heinrich Hertz", "email": "h.hertz@university.edu", "department_id": dept_map["ECE"].id, "designation": "Professor", "specialization": "Electromagnetics"},
            {"employee_id": "FAC_MECH_01", "full_name": "Dr. Rudolf Diesel", "email": "r.diesel@university.edu", "department_id": dept_map["MECH"].id, "designation": "Professor", "specialization": "Thermodynamics"}
        ]
        faculty_map = {}
        for f in faculty_data:
            existing = db.query(Faculty).filter(Faculty.employee_id == f["employee_id"]).first()
            if not existing:
                existing = Faculty(**f)
                db.add(existing)
                db.commit()
                db.refresh(existing)
            faculty_map[f["employee_id"]] = existing

        # 4. Courses
        courses_data = [
            {"code": "CS101", "title": "Introduction to Computer Science", "credits": 4, "department_id": dept_map["CS"].id, "max_capacity": 60, "semester": 1},
            {"code": "CS201", "title": "Data Structures and Algorithms", "credits": 4, "department_id": dept_map["CS"].id, "max_capacity": 50, "semester": 3},
            {"code": "CS301", "title": "Database Management Systems", "credits": 3, "department_id": dept_map["CS"].id, "max_capacity": 55, "semester": 5},
            {"code": "IT102", "title": "Web Application Architecture", "credits": 3, "department_id": dept_map["IT"].id, "max_capacity": 45, "semester": 2},
            {"code": "ECE101", "title": "Digital Signal Processing", "credits": 4, "department_id": dept_map["ECE"].id, "max_capacity": 50, "semester": 4},
            {"code": "MECH101", "title": "Fluid Dynamics and Mechanics", "credits": 4, "department_id": dept_map["MECH"].id, "max_capacity": 40, "semester": 3}
        ]
        course_map = {}
        for c in courses_data:
            existing = db.query(Course).filter(Course.code == c["code"]).first()
            if not existing:
                existing = Course(**c)
                db.add(existing)
                db.commit()
                db.refresh(existing)
            course_map[c["code"]] = existing

        # Prerequisite link: CS201 requires CS101
        if course_map["CS201"].prerequisite_id != course_map["CS101"].id:
            course_map["CS201"].prerequisite_id = course_map["CS101"].id
            db.commit()

        # 5. Students
        students_data = [
            {"register_number": "CS2026001", "first_name": "Eleanor", "last_name": "Vance", "full_name": "Eleanor Vance", "email": "eleanor.vance@university.edu", "phone_number": "9876543201", "department": "Computer Science", "department_id": dept_map["CS"].id, "academic_year": "1st Year", "semester": 1, "status": "active", "gpa": 3.85},
            {"register_number": "CS2026002", "first_name": "Marcus", "last_name": "Aurelius", "full_name": "Marcus Aurelius", "email": "marcus.a@university.edu", "phone_number": "9876543202", "department": "Computer Science", "department_id": dept_map["CS"].id, "academic_year": "2nd Year", "semester": 3, "status": "active", "gpa": 3.90},
            {"register_number": "IT2026001", "first_name": "Ada", "last_name": "Byron", "full_name": "Ada Byron", "email": "ada.byron@university.edu", "phone_number": "9876543203", "department": "Information Technology", "department_id": dept_map["IT"].id, "academic_year": "3rd Year", "semester": 5, "status": "active", "gpa": 4.00},
            {"register_number": "ECE2026001", "first_name": "Nikola", "last_name": "Tesla", "full_name": "Nikola Tesla", "email": "nikola.tesla@university.edu", "phone_number": "9876543204", "department": "Electronics & Communication", "department_id": dept_map["ECE"].id, "academic_year": "4th Year", "semester": 7, "status": "active", "gpa": 3.75},
            {"register_number": "MECH2026001", "first_name": "Leonardo", "last_name": "DaVinci", "full_name": "Leonardo DaVinci", "email": "leonardo@university.edu", "phone_number": "9876543205", "department": "Mechanical Engineering", "department_id": dept_map["MECH"].id, "academic_year": "2nd Year", "semester": 3, "status": "active", "gpa": 3.65},
            {"register_number": "CIVIL2026001", "first_name": "Marie", "last_name": "Curie", "full_name": "Marie Curie", "email": "marie.curie@university.edu", "phone_number": "9876543206", "department": "Civil Engineering", "department_id": dept_map["CIVIL"].id, "academic_year": "1st Year", "semester": 1, "status": "active", "gpa": 3.95}
        ]
        student_map = {}
        for s in students_data:
            existing = db.query(Student).filter(Student.register_number == s["register_number"]).first()
            if not existing:
                existing = Student(**s)
                db.add(existing)
                db.commit()
                db.refresh(existing)
            student_map[s["register_number"]] = existing

        # 6. Enrollments
        for reg, stu in student_map.items():
            crs = course_map["CS101"] if "CS" in reg else (course_map["IT102"] if "IT" in reg else course_map["ECE101"])
            existing_enr = db.query(Enrollment).filter(
                Enrollment.student_id == stu.id,
                Enrollment.course_id == crs.id
            ).first()
            if not existing_enr:
                enr = Enrollment(
                    student_id=stu.id,
                    course_id=crs.id,
                    academic_year="2026-2027",
                    semester=stu.semester,
                    status="enrolled"
                )
                db.add(enr)
                db.commit()

        # 7. Examinations
        exam_cs101 = db.query(Examination).filter(Examination.course_id == course_map["CS101"].id).first()
        if not exam_cs101:
            exam_cs101 = Examination(
                course_id=course_map["CS101"].id,
                title="CS101 Midterm Examination",
                exam_type="midterm",
                exam_date="2026-10-15",
                max_marks=100.0,
                weightage_percent=50.0,
                academic_year="2026-2027",
                semester=1
            )
            db.add(exam_cs101)
            db.commit()
            db.refresh(exam_cs101)

        # 8. Grades
        for reg in ["CS2026001", "CS2026002"]:
            stu = student_map[reg]
            existing_grd = db.query(GradeEntry).filter(
                GradeEntry.examination_id == exam_cs101.id,
                GradeEntry.student_id == stu.id
            ).first()
            if not existing_grd:
                grd = GradeEntry(
                    examination_id=exam_cs101.id,
                    student_id=stu.id,
                    marks_obtained=92.5 if reg == "CS2026001" else 88.0,
                    letter_grade="A+" if reg == "CS2026001" else "A",
                    remarks="Excellent analytical performance",
                    graded_by="Prof. Alan Turing"
                )
                db.add(grd)
                db.commit()

        # 9. Attendance
        for reg, stu in student_map.items():
            crs = course_map["CS101"]
            for day in range(1, 10):
                s_date = f"2026-10-{day:02d}"
                existing_att = db.query(AttendanceRecord).filter(
                    AttendanceRecord.student_id == stu.id,
                    AttendanceRecord.course_id == crs.id,
                    AttendanceRecord.session_date == s_date,
                    AttendanceRecord.slot_number == 1
                ).first()
                if not existing_att:
                    att = AttendanceRecord(
                        student_id=stu.id,
                        course_id=crs.id,
                        session_date=s_date,
                        slot_number=1,
                        status="present" if day != 5 else "late",
                        recorded_by="Prof. Alan Turing"
                    )
                    db.add(att)
            db.commit()

        # 10. Fee Invoices & Payments
        for reg, stu in student_map.items():
            inv_no = f"INV-2026-{reg}"
            existing_inv = db.query(FeeInvoice).filter(FeeInvoice.invoice_number == inv_no).first()
            if not existing_inv:
                inv = FeeInvoice(
                    invoice_number=inv_no,
                    student_id=stu.id,
                    academic_year="2026-2027",
                    semester=stu.semester,
                    title="Tuition & Laboratory Fee Fall 2026",
                    amount=3500.0,
                    waiver_amount=500.0,
                    due_date="2026-11-30",
                    status="partial"
                )
                db.add(inv)
                db.commit()
                db.refresh(inv)

                # Simulated payment
                pay = FeePayment(
                    invoice_id=inv.id,
                    payment_reference=f"PAY-REF-{reg}",
                    amount_paid=1500.0,
                    payment_method="bank_transfer",
                    payment_date="2026-10-01",
                    recorded_by="Finance Bursar",
                    notes="First installment received"
                )
                db.add(pay)
                db.commit()

        # 11. Timetable Slots
        existing_slot = db.query(TimetableSlot).first()
        if not existing_slot:
            slot = TimetableSlot(
                course_id=course_map["CS101"].id,
                faculty_id=faculty_map["FAC_CS_01"].id,
                classroom_id=classroom_map["LH-101"].id,
                day_of_week="Monday",
                start_time="09:00",
                end_time="10:30",
                academic_year="2026-2027",
                semester=1
            )
            db.add(slot)
            db.commit()

        logger.info("Synthetic seed completed successfully. Repeatable & verified.")
    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
