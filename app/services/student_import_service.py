"""
Bulk Student CSV Import Service: Template Generation, File Validation,
Intra-file & Database Duplicate Detection, Transaction-Safe Import,
and Sanitized Error Reporting.
"""

import csv
import io
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.student import Student
from app.repositories.student_repo import StudentRepository
from app.repositories.audit_repo import AuditRepository
from app.schemas.student import (
    StudentCSVRow,
    StudentCSVImportPreviewResponse,
    StudentCSVImportResult,
    StudentResponse
)
from app.utils.validators import validate_email, normalize_register_number
from app.utils.csv_export import sanitize_csv_cell, generate_safe_csv
from app.core.exceptions import ValidationException

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB limit
VALID_STATUSES = {"applicant", "active", "suspended", "graduated", "withdrawn"}
REQUIRED_COLUMNS = [
    "register_number",
    "full_name",
    "email",
    "phone_number",
    "department",
    "academic_year"
]
OPTIONAL_COLUMNS = [
    "semester",
    "status",
    "gpa",
    "date_of_birth",
    "gender",
    "guardian_name",
    "guardian_phone",
    "address"
]
ALL_TEMPLATE_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


class StudentCSVImportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = StudentRepository(db)
        self.audit_repo = AuditRepository(db)

    @staticmethod
    def get_csv_template() -> str:
        """
        Generate an RFC 4180 compliant CSV template with required headers
        and fictional example data.
        """
        sample_rows = [
            {
                "register_number": "CS2026101",
                "full_name": "Amina Chen",
                "email": "amina.chen@university.edu",
                "phone_number": "9876543210",
                "department": "Computer Science",
                "academic_year": "1st Year",
                "semester": "1",
                "status": "active",
                "gpa": "3.85",
                "date_of_birth": "2005-04-12",
                "gender": "Female",
                "guardian_name": "Wei Chen",
                "guardian_phone": "9876543299",
                "address": "123 Academic Way, Metropolis"
            },
            {
                "register_number": "IT2026102",
                "full_name": "Carlos Ramirez",
                "email": "carlos.ramirez@university.edu",
                "phone_number": "9876543211",
                "department": "Information Technology",
                "academic_year": "2nd Year",
                "semester": "3",
                "status": "active",
                "gpa": "3.70",
                "date_of_birth": "2004-09-23",
                "gender": "Male",
                "guardian_name": "Elena Ramirez",
                "guardian_phone": "9876543298",
                "address": "456 Tech Boulevard, Silicon Valley"
            }
        ]
        return generate_safe_csv(ALL_TEMPLATE_COLUMNS, sample_rows)

    def parse_and_validate_csv(
        self,
        file_bytes: bytes,
        filename: str = "upload.csv"
    ) -> Tuple[List[StudentCSVRow], List[Dict[str, Any]]]:
        """
        Parse and validate CSV content, returning validated preview rows
        and a detailed error summary.
        """
        # 1. File size validation
        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValidationException(
                f"File size ({len(file_bytes)} bytes) exceeds the maximum allowed limit of 5MB.",
                status_code=400
            )

        # 2. File extension validation
        if not filename.lower().endswith(".csv"):
            raise ValidationException(
                "Invalid file format. Only standard CSV files (.csv) are accepted.",
                status_code=400
            )

        # 3. Empty file check
        if len(file_bytes.strip()) == 0:
            raise ValidationException(
                "The uploaded CSV file is empty. Please provide a file with student records.",
                status_code=400
            )

        # 4. Decoding check (support UTF-8 and UTF-8 with BOM)
        try:
            content = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                content = file_bytes.decode("latin-1")
            except Exception:
                raise ValidationException(
                    "Unable to decode file content. Please upload a UTF-8 encoded CSV file.",
                    status_code=400
                )

        # 5. CSV Parsing
        try:
            reader = csv.reader(io.StringIO(content))
            all_lines = list(reader)
        except Exception as e:
            raise ValidationException(
                f"Malformed CSV file structure: {str(e)}",
                status_code=400
            )

        # Remove trailing empty lines
        while all_lines and not any(cell.strip() for cell in all_lines[-1]):
            all_lines.pop()

        if not all_lines:
            raise ValidationException(
                "The uploaded CSV file contains no readable lines.",
                status_code=400
            )

        # 6. Header validation
        header_row = [c.strip().lower() for c in all_lines[0]]
        header_map = {col: idx for idx, col in enumerate(header_row)}

        missing_columns = [col for col in REQUIRED_COLUMNS if col not in header_map]
        if missing_columns:
            raise ValidationException(
                f"CSV header is missing required column(s): {', '.join(missing_columns)}. "
                f"Required headers are: {', '.join(REQUIRED_COLUMNS)}.",
                status_code=400
            )

        data_rows = all_lines[1:]
        if not data_rows:
            raise ValidationException(
                "The CSV file contains column headers but no data records to import.",
                status_code=400
            )

        # 7. Row-by-row validation & duplicate tracking
        parsed_rows: List[StudentCSVRow] = []
        error_summary: List[Dict[str, Any]] = []

        seen_reg_numbers: Set[str] = set()
        seen_emails: Set[str] = set()

        for idx, row in enumerate(data_rows, start=2):
            # Skip empty lines
            if not any(cell.strip() for cell in row):
                continue

            row_errors: List[str] = []
            is_duplicate = False
            duplicate_reason: Optional[str] = None

            def get_val(col_name: str) -> str:
                pos = header_map.get(col_name)
                if pos is not None and pos < len(row):
                    return row[pos].strip()
                return ""

            raw_reg = get_val("register_number")
            raw_name = get_val("full_name")
            raw_email = get_val("email")
            raw_phone = get_val("phone_number")
            raw_dept = get_val("department")
            raw_year = get_val("academic_year")
            raw_sem = get_val("semester") or "1"
            raw_status = get_val("status") or "active"
            raw_gpa = get_val("gpa") or "0.0"
            raw_dob = get_val("date_of_birth") or None
            raw_gender = get_val("gender") or None
            raw_guardian = get_val("guardian_name") or None
            raw_gphone = get_val("guardian_phone") or None
            raw_address = get_val("address") or None

            # --- Field Validation ---
            # Register number
            if not raw_reg:
                row_errors.append("Registration number is required.")
            elif len(raw_reg) < 2 or len(raw_reg) > 50:
                row_errors.append("Registration number must be between 2 and 50 characters.")
            norm_reg = normalize_register_number(raw_reg) if raw_reg else ""

            # Full name
            if not raw_name:
                row_errors.append("Full name is required.")
            elif len(raw_name) < 2 or len(raw_name) > 100:
                row_errors.append("Full name must be between 2 and 100 characters.")

            # Email
            clean_email = raw_email.lower()
            if not raw_email:
                row_errors.append("Email address is required.")
            elif not validate_email(clean_email):
                row_errors.append(f"Invalid email format: '{raw_email}'.")

            # Phone number (10 digits)
            clean_phone = re.sub(r"\D", "", raw_phone)
            if not raw_phone:
                row_errors.append("Phone number is required.")
            elif len(clean_phone) != 10:
                row_errors.append(
                    f"Phone number must be exactly 10 numeric digits. Received {len(clean_phone)} digits."
                )

            # Department
            if not raw_dept:
                row_errors.append("Department is required.")
            elif len(raw_dept) < 2 or len(raw_dept) > 100:
                row_errors.append("Department name must be between 2 and 100 characters.")

            # Academic year
            if not raw_year:
                row_errors.append("Academic year is required.")
            elif len(raw_year) < 2 or len(raw_year) > 50:
                row_errors.append("Academic year must be between 2 and 50 characters.")

            # Semester (integer 1..8)
            try:
                sem_val = int(raw_sem)
                if sem_val < 1 or sem_val > 8:
                    row_errors.append("Semester must be an integer between 1 and 8.")
            except ValueError:
                row_errors.append(f"Invalid semester number '{raw_sem}'. Must be 1 to 8.")
                sem_val = 1

            # Status
            status_val = raw_status.lower()
            if status_val not in VALID_STATUSES:
                row_errors.append(
                    f"Invalid status '{raw_status}'. Allowed: {', '.join(sorted(VALID_STATUSES))}."
                )
                status_val = "active"

            # GPA (0.0 .. 4.0)
            try:
                gpa_val = float(raw_gpa)
                if gpa_val < 0.0 or gpa_val > 4.0:
                    row_errors.append("GPA must be between 0.00 and 4.00.")
            except ValueError:
                row_errors.append(f"Invalid GPA value '{raw_gpa}'. Must be numeric.")
                gpa_val = 0.0

            # --- Duplicate Checks (Intra-file and Database) ---
            if norm_reg:
                if norm_reg in seen_reg_numbers:
                    is_duplicate = True
                    duplicate_reason = f"Duplicate register number within CSV file: '{norm_reg}'."
                    row_errors.append(duplicate_reason)
                else:
                    seen_reg_numbers.add(norm_reg)
                    # Check database duplicate
                    if self.repo.get_by_register_number(norm_reg):
                        is_duplicate = True
                        duplicate_reason = f"Register number '{norm_reg}' already exists in the system database."
                        row_errors.append(duplicate_reason)

            if clean_email and validate_email(clean_email):
                if clean_email in seen_emails:
                    is_duplicate = True
                    reason = f"Duplicate email address within CSV file: '{clean_email}'."
                    duplicate_reason = (duplicate_reason + "; " + reason) if duplicate_reason else reason
                    row_errors.append(reason)
                else:
                    seen_emails.add(clean_email)
                    # Check database duplicate
                    if self.repo.get_by_email(clean_email):
                        is_duplicate = True
                        reason = f"Email '{clean_email}' already exists in the system database."
                        duplicate_reason = (duplicate_reason + "; " + reason) if duplicate_reason else reason
                        row_errors.append(reason)

            is_valid = len(row_errors) == 0

            # Log to error summary
            if not is_valid:
                for err in row_errors:
                    error_summary.append({
                        "row_number": idx,
                        "register_number": norm_reg or raw_reg or "N/A",
                        "full_name": raw_name or "N/A",
                        "email": raw_email or "N/A",
                        "error_message": err,
                        "is_duplicate": is_duplicate
                    })

            csv_row = StudentCSVRow(
                row_number=idx,
                register_number=norm_reg or raw_reg,
                full_name=raw_name,
                email=clean_email or raw_email,
                phone_number=clean_phone or raw_phone,
                department=raw_dept,
                academic_year=raw_year,
                semester=sem_val,
                status=status_val,
                gpa=gpa_val,
                date_of_birth=raw_dob,
                gender=raw_gender,
                guardian_name=raw_guardian,
                guardian_phone=raw_gphone,
                address=raw_address,
                is_valid=is_valid,
                is_duplicate=is_duplicate,
                duplicate_reason=duplicate_reason,
                errors=row_errors
            )
            parsed_rows.append(csv_row)

        return parsed_rows, error_summary

    def preview_import(
        self,
        file_bytes: bytes,
        filename: str = "upload.csv"
    ) -> StudentCSVImportPreviewResponse:
        """
        Validate CSV and return preview metadata without committing any database changes.
        """
        rows, error_summary = self.parse_and_validate_csv(file_bytes, filename)
        valid_count = sum(1 for r in rows if r.is_valid)
        duplicate_count = sum(1 for r in rows if r.is_duplicate)
        invalid_count = len(rows) - valid_count

        return StudentCSVImportPreviewResponse(
            total_rows=len(rows),
            valid_rows_count=valid_count,
            invalid_rows_count=invalid_count,
            duplicate_rows_count=duplicate_count,
            preview_rows=rows,
            error_summary=error_summary
        )

    def import_students_from_csv(
        self,
        file_bytes: bytes,
        filename: str = "upload.csv",
        allow_partial: bool = True,
        current_username: Optional[str] = "admin"
    ) -> StudentCSVImportResult:
        """
        Execute student import from CSV.
        If allow_partial is False and any record is invalid or duplicate,
        aborts entirely without modifying the database.
        Wraps imports in an atomic transaction.
        """
        rows, error_summary = self.parse_and_validate_csv(file_bytes, filename)

        valid_rows = [r for r in rows if r.is_valid]
        duplicate_count = sum(1 for r in rows if r.is_duplicate)
        failed_count = len(rows) - len(valid_rows)

        if not allow_partial and failed_count > 0:
            raise ValidationException(
                f"CSV import failed: {failed_count} row(s) contain validation errors or duplicates, "
                f"and partial imports are disabled.",
                status_code=400
            )

        if not valid_rows:
            return StudentCSVImportResult(
                total_rows=len(rows),
                imported_count=0,
                failed_count=failed_count,
                duplicate_count=duplicate_count,
                imported_students=[],
                errors=error_summary
            )

        imported_students: List[StudentResponse] = []

        try:
            # Use nested transaction for safe rollback if needed
            with self.db.begin_nested():
                for r in valid_rows:
                    student = Student(
                        register_number=r.register_number,
                        full_name=r.full_name,
                        email=r.email,
                        phone_number=r.phone_number,
                        department=r.department,
                        academic_year=r.academic_year,
                        semester=r.semester,
                        status=r.status,
                        gpa=r.gpa,
                        date_of_birth=r.date_of_birth,
                        gender=r.gender,
                        guardian_name=r.guardian_name,
                        guardian_phone=r.guardian_phone,
                        address=r.address
                    )
                    self.db.add(student)
                    self.db.flush()
                    imported_students.append(StudentResponse.model_validate(student))

            self.db.commit()

            # Log audit event without logging passwords, tokens, or sensitive personal data
            self.audit_repo.log_event(
                action="BULK_IMPORT",
                entity_type="Student",
                entity_id=str(len(imported_students)),
                username=current_username,
                new_values=f"Imported {len(imported_students)} students from '{filename}'"
            )

        except SQLAlchemyError as db_err:
            self.db.rollback()
            raise ValidationException(
                f"Database error during bulk student import: {str(db_err)}",
                status_code=500
            )

        return StudentCSVImportResult(
            total_rows=len(rows),
            imported_count=len(imported_students),
            failed_count=failed_count,
            duplicate_count=duplicate_count,
            imported_students=imported_students,
            errors=error_summary
        )

    @staticmethod
    def generate_error_report_csv(errors: List[Dict[str, Any]]) -> str:
        """
        Generate a downloadable CSV error report with CSV injection protection.
        """
        fieldnames = ["row_number", "register_number", "full_name", "email", "error_message", "is_duplicate"]
        return generate_safe_csv(fieldnames, errors)
