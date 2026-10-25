# EduTrack Enterprise — Advanced Student Information & Academic Management Platform

An enterprise-grade, full-stack Student Information and Academic Management Platform engineered with **FastAPI**, **SQLAlchemy 2.0 ORM**, **Pydantic v2**, and a modern **Vanilla HTML5 / CSS3 / JavaScript** single-page administration dashboard. Built for realistic institutional operations with RBAC, attendance percentage shortage tracking, examination grading schemas, tuition ledgers with overpayment protection, conflict-aware course timetabling, safe CSV exports, and **1,140+ automated automated tests**.

---

## 🏛️ System Architecture & Modularity

The application follows a clean layered domain architecture with strict separation of concerns:

```
student-management/
    app/
        main.py                     # Application entry point, middleware & route mounting
        core/
            config.py               # Application settings & environment configurations
            security.py             # PBKDF2 password hashing & JWT token verification
            permissions.py          # Role definitions (Admin, Faculty, Student, Finance)
            logging.py              # Structured application logger
            exceptions.py           # Domain exceptions with HTTP status mapping
        database/
            base.py                 # SQLAlchemy Declarative Base
            session.py              # Engine, connection pooling & SessionLocal
            init_db.py              # Schema creation & baseline seed data
        models/                     # Normalized database models
            user.py, student.py, department.py, faculty.py, course.py,
            enrollment.py, attendance.py, examination.py, grade.py,
            fee.py, timetable.py, audit_log.py, notification.py
        schemas/                    # Pydantic v2 validation models
            common.py, user.py, student.py, department.py, faculty.py, course.py,
            enrollment.py, attendance.py, examination.py, grade.py, fee.py,
            timetable.py, audit_log.py, notification.py, analytics.py
        repositories/               # Data access layer & indexed queries
            base.py, student_repo.py, user_repo.py, course_repo.py,
            enrollment_repo.py, attendance_repo.py, grade_repo.py,
            fee_repo.py, timetable_repo.py, audit_repo.py, notification_repo.py
        services/                   # Pure domain business logic & transactions
            auth_service.py, student_service.py, academic_service.py,
            enrollment_service.py, attendance_service.py, grade_service.py,
            fee_service.py, timetable_service.py, analytics_service.py, export_service.py
        middleware/
            rate_limit.py           # Sliding-window in-memory rate limiter
            error_handler.py        # Global domain exception handler
        static/                     # University administration GUI
            index.html              # Responsive single-page application dashboard
            style.css               # Professional dark navy, deep blue, and slate design tokens
            script.js               # Reactive client-side application controller
    tests/                          # 1,140+ Automated Pytest Test Suite
        conftest.py                 # In-memory SQLite with StaticPool & TestClient fixtures
        test_manifest.py            # Test category targets and distribution audit
        unit/                       # 840+ Unit test cases
            test_student_admissions.py
            test_authentication_permissions.py
            test_departments_courses_faculty.py
            test_enrollment_prerequisites.py
            test_attendance_workflows.py
            test_examinations_grades.py
            test_fees_payments.py
            test_timetable_conflicts.py
            test_analytics_exports.py
        database/                   # Database constraints & transactions (40 cases)
            test_constraints_transactions.py
        api/                        # API integration & validation tests (120+ cases)
            test_api_validation_errors.py
            test_full_academic_workflows.py
        security/                   # Security, RBAC & negative tests (50 cases)
            test_security_negative.py
        performance/                # Benchmark performance tests (1,000 synthetic records)
            test_performance_benchmarks.py
    scripts/
        seed_data.py                # Repeatable synthetic seed script
        demo_scenario.py            # End-to-end executable lifecycle demonstration
    Dockerfile
    docker-compose.yml
    requirements.txt
    pyproject.toml
    pytest.ini
    .env.example
```

---

## 🎨 Professional University Administration GUI

The dashboard features a dark navy (`#0f172a`), deep royal blue (`#1e3a8a`, `#2563eb`), and crisp white visual system:
- **Responsive Drawer Sidebar**: Collapsible navigation with quick badges and system health indicator.
- **Header with Debounced Search**: Global search input filtering across student name, register number, and email.
- **Real-Time KPI Cards**: Total students, active enrollments, course count, faculty allocation, attendance %, and tuition fee balances.
- **Interactive Visualizations**: Dynamic Chart.js visualizations for department distribution and examination grade performance.
- **Student Records Directory**: Full pagination, multi-column search, department filter, year filter, status filter, and student dossier view.
- **Multi-Step Admissions Wizard**: 3-step form (Personal -> Academic -> Contact/Guardian) with live validation.
- **Attendance Interface**: Period/slot selector, bulk radio marking (Present, Late, Absent, Excused), and shortage calculations.
- **Examinations & Grading**: Weighted assessment setup, marks entry, and mandatory reason auditing for grade amendments.
- **Fee Ledger**: Invoice tracking, partial payments, and backend-enforced overpayment rejection.
- **Scheduling & Timetable**: Time matrix with conflict detection for classroom and faculty double-booking.
- **Audit Log Viewer**: Real-time event log tracking sensitive administrative mutations.

---

## 🏛️ Real University Business Rules & Dependency-Based Workflows

EduTrack enforces strict real-world academic workflows, eligibility preconditions, record dependencies, and lifecycle safeguards rather than isolated record mutations.

### 1. Department & Faculty Governance (HOD Hierarchy)
- **Parent Dependency**: An academic department must exist and be active before faculty can be appointed to it.
- **HOD Appointment Eligibility**: An appointed Head of Department (HOD) must be an existing, active faculty member who belongs directly to that specific department (`faculty.department_id == department.id`).
- **Single Chair Rule**: Exactly one active HOD is permitted per department, and a single faculty member cannot simultaneously hold HOD chairs in multiple departments.
- **Transfer Resolution**: If a faculty member is transferred to another department, their previous HOD assignment is automatically vacated to prevent cross-department governance inconsistencies.
- **Safe Deletion & Archival**: Deletion of a department is blocked if active faculty members, courses, or students are assigned. Faculty deletion is blocked if the instructor is actively serving as an HOD or has assigned timetable slots.

### 2. Curriculum & Prerequisite Graph Rules
- **Cycle Detection**: Circular prerequisite chains (e.g. $A \rightarrow B \rightarrow A$ or $A \rightarrow B \rightarrow C \rightarrow A$) and self-prerequisites ($A \rightarrow A$) are detected via graph traversal and rejected before insertion.
- **Active Course Prerequisite**: Only active courses can be linked as prerequisites for subsequent courses.
- **Safe Curriculum Deletion**: A course cannot be deleted if other courses list it as a prerequisite, if student enrollments exist, or if scheduled examinations/timetable slots depend on it.

### 3. Student Admission & Course Enrollment Rules
- **Active Status Enforcement**: Only students with status `active` are eligible for course registration. Suspended, graduated, or withdrawn students are rejected.
- **Single Concurrent Enrollment**: A student cannot enroll in the same course twice while an active enrollment exists.
- **Completed Course Retake Policy**: Institutional policy prevents retaking courses already completed with a passing grade ($GPA \ge 2.0$).
- **Prerequisite Completion**: Enrollment requires that all prerequisite courses have been completed with a passing grade ($GPA \ge 2.0$).
- **Capacity Locking**: Enforces class seat thresholds (`max_capacity`) atomically.
- **Financial & Enrollment Deletion Protection**: A student record cannot be deleted if active enrollments exist or if unpaid fee invoices remain outstanding.

### 4. Attendance & Examination Integrity
- **Enrollment Dependency**: Attendance sessions and examination marks can only be recorded for students with an active `Enrollment` in that specific course.
- **Assessment Mark Bounds**: Marks obtained must be non-negative and cannot exceed the examination's configured maximum marks ($0 \le \text{marks} \le \text{max\_marks}$).
- **Audit Amendments**: Any grade modification requires mandatory textual justification logged directly into the system audit trail.

### 5. Scheduling & Timetable Governance
- **Instructor Verification**: Scheduled faculty members must exist, be active, and belong to the course's academic department.
- **Double-Booking Prevention**: Detects and rejects both room collision (same room at overlapping time) and instructor collision (same faculty scheduled simultaneously in different rooms).
- **Interval Chronology**: Requires `start_time < end_time` with validated 24-hour time formats.

### 6. Financial Ledger & Overpayment Safeguards
- **Balance Calculation**: Invoices calculate net balance accounting for institutional fee waivers.
- **Overpayment Rejection**: Payments exceeding the current outstanding invoice balance are strictly rejected.

---

## 📋 Dependency Matrix

| Prerequisite Record | Required Precondition | Failure / Rejection Outcome | Verifying Test Case |
| :--- | :--- | :--- | :--- |
| **Department** | Must exist and be active before faculty assignment | HTTP 404 / 400 (`Department not found` / `inactive`) | `test_cannot_create_faculty_for_nonexistent_department` |
| **Faculty Member** | Must exist, be active, and belong to department to be HOD | HTTP 400 (`Faculty belongs to department #X, not #Y`) | `test_cannot_assign_hod_from_different_department` |
| **Faculty Member** | Status must be active (not terminated/inactive) for HOD | HTTP 400 (`status is inactive or terminated`) | `test_cannot_assign_inactive_faculty_as_hod` |
| **Department Chair** | Department can only have 1 active HOD; 1 chair per person | HTTP 400 (`already serving as Head of Department`) | `test_cannot_assign_faculty_as_hod_of_multiple_departments` |
| **Faculty Transfer** | Transferring faculty vacates old department HOD chair | Old department HOD becomes vacant (`null`) | `test_faculty_transfer_vacates_old_department_hod` |
| **Department Deletion** | No dependent faculty, courses, or students may exist | HTTP 400 (`Contains associated faculty/course/student`) | `test_cannot_delete_department_with_faculty` |
| **Faculty Deletion** | Cannot delete faculty actively serving as HOD or scheduled | HTTP 400 (`Currently serving as Head of Department`) | `test_cannot_delete_faculty_serving_as_hod` |
| **Course Prerequisite** | A course cannot have itself as a prerequisite ($A \rightarrow A$) | HTTP 400 (`A course cannot have itself as a prerequisite`) | `test_cannot_set_course_self_prerequisite` |
| **Course Prerequisite** | Circular prerequisite loops ($A \rightarrow B \rightarrow A$) forbidden | HTTP 400 (`Circular prerequisite dependency detected`) | `test_cannot_set_direct_circular_prerequisite` |
| **Course Deletion** | Cannot delete course if prerequisite for other courses | HTTP 400 (`It is a prerequisite for: ...`) | `test_cannot_delete_course_with_dependent_courses` |
| **Course Enrollment** | Student status must be `active` (not suspended/graduated) | HTTP 400 (`Cannot enroll student with status 'suspended'`) | `test_cannot_enroll_inactive_student` |
| **Course Enrollment** | Student cannot be concurrently enrolled in same course | HTTP 400 (`already actively enrolled in course`) | `test_cannot_enroll_twice_in_same_course` |
| **Course Enrollment** | Prerequisite course must be completed with $GPA \ge 2.0$ | HTTP 400 (`Prerequisite CS100 not satisfied`) | `test_prerequisite_grade_thresholds` |
| **Course Enrollment** | Class capacity cannot exceed `max_capacity` | HTTP 400 (`Capacity exceeded for course`) | `test_capacity_limits` |
| **Student Deletion** | Cannot delete student with active enrollments | HTTP 400 (`Student has active course enrollment(s)`) | `test_cannot_delete_student_with_active_enrollments` |
| **Student Deletion** | Cannot delete student with unpaid fee invoices | HTTP 400 (`Student has outstanding/unpaid fee invoice(s)`) | `test_student_service_delete_safeguards` |
| **Attendance Record** | Student must have an active `Enrollment` in the course | HTTP 400 (`Student is not actively enrolled in Course`) | `test_cannot_record_attendance_for_non_enrolled_student` |
| **Attendance Record** | Session date and slot number must be unique per student | HTTP 400 (`AttendanceRecord already exists for session`) | `test_duplicate_attendance_session_prevention` |
| **Examination Grade** | Student must be enrolled in the examination's course | HTTP 400 (`Student is not enrolled in the course for Exam`) | `test_cannot_record_grade_for_non_enrolled_student` |
| **Examination Grade** | Marks obtained must satisfy $0.0 \le \text{marks} \le \text{max\_marks}$ | HTTP 400 (`Marks cannot exceed exam maximum marks`) | `test_cannot_record_grade_exceeding_max_marks` |
| **Timetable Slot** | Faculty must exist, be active, and match course department | HTTP 400 / 404 (`inactive faculty member` / `not found`) | `test_cannot_schedule_slot_for_inactive_faculty` |
| **Timetable Slot** | Classroom and faculty cannot be double-booked | HTTP 409 (`Schedule conflict detected for room/faculty`) | `test_classroom_conflict_detection` |
| **Fee Invoice Payment**| Payment amount cannot exceed outstanding balance | HTTP 400 (`Payment amount exceeds outstanding balance`) | `test_cannot_overpay_fee_invoice` |

---

## 🧪 Comprehensive Automated Test Suite (1,213 Tests)

The repository includes an extensive automated test suite executed via `pytest`:

```bash
# 1. Collect all test items
pytest --collect-only -q
# Output: 1213 tests collected

# 2. Run complete test suite
pytest -q
# Output: 1213 passed, 1 warning in 39s

# 3. Generate detailed code coverage report
pytest -q --cov=app --cov-report=term-missing
# Output: 88% Total Application Code Coverage
```

### Test Distribution Across Categories

| Category | Cases | File |
| :--- | :--- | :--- |
| **Student Management & Admissions** | 150 | `tests/unit/test_student_admissions.py` |
| **Authentication & Permissions** | 120 | `tests/unit/test_authentication_permissions.py` |
| **Departments, Courses & Faculty** | 120 | `tests/unit/test_departments_courses_faculty.py` |
| **Enrollment & Prerequisites** | 120 | `tests/unit/test_enrollment_prerequisites.py` |
| **Attendance Calculations & Workflows** | 120 | `tests/unit/test_attendance_workflows.py` |
| **Examinations & Grade Calculations** | 120 | `tests/unit/test_examinations_grades.py` |
| **Fees, Payments & Scholarships** | 100 | `tests/unit/test_fees_payments.py` |
| **Timetable & Conflict Detection** | 70 | `tests/unit/test_timetable_conflicts.py` |
| **Analytics, Rollups & Safe CSV Exports** | 50 | `tests/unit/test_analytics_exports.py` |
| **Database Constraints & Integrity** | 40 | `tests/database/test_constraints_transactions.py` |
| **API Validation Errors & HTTP Codes** | 50 | `tests/api/test_api_validation_errors.py` |
| **Security & Negative Authorization** | 50 | `tests/security/test_security_negative.py` |
| **End-to-End Academic Workflows** | 7 | `tests/api/test_full_academic_workflows.py` |
| **Real University Workflow & Dependency Rules** | **21** | `tests/api/test_university_workflows.py` |
| **Bulk CSV Import Services & Validation** | 20 | `tests/unit/test_student_csv_service.py` |
| **Bulk CSV Import Endpoints & RBAC** | 23 | `tests/api/test_student_csv_import.py` |
| **Test Manifest & Planning Audit** | 13 | `tests/test_manifest.py` |
| **Legacy Compatibility Tests** | 19 | `tests/test_main.py` |
| **TOTAL** | **1,213** | **100% Passing** |

---

## 🚀 Installation & Local Execution

### 1. Environment Setup
```bash
# Navigate to project directory
cd student-management

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Database Seeding
Populate realistic synthetic data (idempotent and safe to run multiple times):
```bash
python scripts/seed_data.py
```

### 3. Run Demonstration Scenario
Execute the complete end-to-end academic lifecycle test:
```bash
python scripts/demo_scenario.py
```

### 4. Start the Application Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **Web Dashboard GUI**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📊 Performance Benchmarks

Run dedicated latency and query throughput benchmarks on 1,000 synthetic records:
```bash
pytest -s tests/performance/test_performance_benchmarks.py
```
**Empirical Results (Windows / SQLite In-Memory):**
- Full-text search across 1,000 records: `21.42 ms`
- Deep pagination (offset 800): `10.51 ms`
- Department analytics rollup: `5.88 ms`

---

## 📂 Bulk Student Import from CSV

The platform features an enterprise-grade **Bulk Student Import from CSV** engine, providing administrators with automated roster intake, validation previews, intra-file and database duplicate detection, atomic database transactions, and formula-injection safe error reporting.

### 1. Key Capabilities

- **Strict Schema Validation**: Validates required headers, email RFC formats, exactly 10-digit phone numbers, semester ranges ($1..8$), and GPA bounds ($0.00..4.00$).
- **Intra-File & Database Duplicate Detection**: Detects and highlights collisions both within the uploaded file (e.g. repeated student numbers or emails) and against existing database records.
- **Pre-Import Inspection (Dry Run)**: Allows administrators to preview valid, duplicate, and invalid records with row-by-row error messages before committing any database writes.
- **Flexible Transactional Import**:
  - `allow_partial=True` (default): Atomically inserts all valid, non-duplicate records while skipping and reporting invalid rows.
  - `allow_partial=False`: Enforces an all-or-nothing policy; if any row fails validation or duplicate check, the entire import is rolled back.
- **Formula Injection Defense**: All downloadable error reports sanitize cells starting with spreadsheet command prefixes (`=`, `+`, `-`, `@`, `\t`, `\r`) with leading single quotes.
- **Audit Logging**: Each bulk import records an audit event logging the total records imported and the responsible administrator, strictly omitting passwords, tokens, or sensitive student PII.
- **RBAC Protection**: Administrative import endpoints require `Role.ADMIN`, strictly forbidding unauthorized or unauthenticated requests.

### 2. CSV Column Specification

| Column | Type | Required? | Constraints & Format |
| :--- | :--- | :--- | :--- |
| `register_number` | String | **Yes** | 2–50 chars, unique, normalized uppercase (e.g., `CS2026101`) |
| `full_name` | String | **Yes** | 2–100 chars, legal full name |
| `email` | String | **Yes** | Valid RFC email format, unique across students |
| `phone_number` | String | **Yes** | Exactly 10 numeric digits (e.g., `9876543210`) |
| `department` | String | **Yes** | 2–100 chars, academic department name |
| `academic_year` | String | **Yes** | 2–50 chars (e.g., `1st Year`, `2026-2027`) |
| `semester` | Integer | No | Integer from 1 to 8 (defaults to `1`) |
| `status` | String | No | `applicant`, `active`, `suspended`, `graduated`, `withdrawn` (defaults to `active`) |
| `gpa` | Float | No | Decimal from `0.00` to `4.00` (defaults to `0.00`) |
| `date_of_birth` | String | No | ISO format date (`YYYY-MM-DD`) |
| `gender` | String | No | Gender identity (`Female`, `Male`, `Other`) |
| `guardian_name` | String | No | Emergency contact / guardian legal name |
| `guardian_phone`| String | No | Contact phone number for guardian |
| `address` | String | No | Residential mailing address |

### 3. API Endpoints

- **Download CSV Template**:
  ```http
  GET /api/v1/students/csv-template
  ```
  Returns `student_import_template.csv` with required headers and fictional example rows.

- **Pre-Import Inspection (Preview)**:
  ```http
  POST /api/v1/students/import-csv/preview
  Authorization: Bearer <ADMIN_TOKEN>
  Content-Type: multipart/form-data
  ```

- **Execute Bulk Import**:
  ```http
  POST /api/v1/students/import-csv
  Authorization: Bearer <ADMIN_TOKEN>
  Content-Type: multipart/form-data
  FormData:
    file: <students.csv>
    allow_partial: true
  ```

- **Download Sanitized Error Report**:
  ```http
  POST /api/v1/students/import-csv/error-report
  Authorization: Bearer <ADMIN_TOKEN>
  Content-Type: application/json
  Body:
    { "errors": [ ... ] }
  ```

### 4. Fictional Example CSV Data

```csv
register_number,full_name,email,phone_number,department,academic_year,semester,status,gpa,date_of_birth,gender
CS2026101,Amina Chen,amina.chen@university.edu,9876543210,Computer Science,1st Year,1,active,3.85,2005-04-12,Female
IT2026102,Carlos Ramirez,carlos.ramirez@university.edu,9876543211,Information Technology,2nd Year,3,active,3.70,2004-09-23,Male
ECE2026103,Fatima Al-Mansoor,fatima.m@university.edu,9876543212,Electronics & Communication,3rd Year,5,active,3.92,2003-11-18,Female
MECH2026104,Liam O'Connor,liam.oconnor@university.edu,9876543213,Mechanical Engineering,1st Year,1,active,3.60,2005-08-30,Male
CIVIL2026105,Priya Patel,priya.patel@university.edu,9876543214,Civil Engineering,4th Year,7,active,3.98,2002-06-15,Female
```

---

## 🔒 Default System Credentials (Synthetic Development)

| Role | Username | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@12345` | Full System Access |
| **Faculty** | `faculty` | `Faculty@12345` | Grading, Attendance, Courses |
| **Finance** | `finance` | `Finance@12345` | Invoices, Payments, Ledgers |
