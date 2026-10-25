"""
Unit tests for StudentCSVImportService.
Tests template generation, CSV parsing, duplicate detection, and sanitization at the service layer.
"""

import pytest
from sqlalchemy.orm import Session
from app.services.student_import_service import StudentCSVImportService
from app.models.student import Student
from app.core.exceptions import ValidationException


def test_service_template_generation():
    """Verify CSV template contains proper headers and RFC 4180 structure."""
    template = StudentCSVImportService.get_csv_template()
    assert "register_number,full_name,email,phone_number" in template
    assert "Amina Chen" in template
    assert "Carlos Ramirez" in template


def test_service_parse_valid_csv(db_session: Session):
    """Test service parsing a valid CSV file."""
    csv_bytes = (
        "register_number,full_name,email,phone_number,department,academic_year\r\n"
        "SRV001,John Doe,john.doe@univ.edu,9876543210,Computer Science,1st Year\r\n"
    ).encode("utf-8")

    service = StudentCSVImportService(db_session)
    rows, errors = service.parse_and_validate_csv(csv_bytes, "students.csv")

    assert len(rows) == 1
    assert len(errors) == 0
    assert rows[0].is_valid is True
    assert rows[0].register_number == "SRV001"
    assert rows[0].phone_number == "9876543210"


def test_service_empty_bytes_raises_validation_exception(db_session: Session):
    """Empty byte input must raise ValidationException."""
    service = StudentCSVImportService(db_session)
    with pytest.raises(ValidationException) as exc_info:
        service.parse_and_validate_csv(b"", "empty.csv")
    assert "empty" in str(exc_info.value.detail).lower()


def test_service_missing_column_raises_validation_exception(db_session: Session):
    """Missing required column must raise ValidationException listing the column."""
    csv_bytes = "register_number,full_name\r\nSRV001,John\r\n".encode("utf-8")
    service = StudentCSVImportService(db_session)
    with pytest.raises(ValidationException) as exc_info:
        service.parse_and_validate_csv(csv_bytes, "incomplete.csv")
    assert "missing required column" in str(exc_info.value.detail).lower()


def test_service_preview_counts_metrics(db_session: Session):
    """Verify preview_import calculates counts of valid, invalid, duplicate rows accurately."""
    csv_bytes = (
        "register_number,full_name,email,phone_number,department,academic_year\r\n"
        "METRIC01,Good One,good1@univ.edu,9876543210,CS,1st Year\r\n"
        "METRIC01,Duplicate Reg,dup@univ.edu,9876543211,CS,1st Year\r\n"
        "METRIC02,Bad Phone,good2@univ.edu,123,CS,1st Year\r\n"
    ).encode("utf-8")

    service = StudentCSVImportService(db_session)
    preview = service.preview_import(csv_bytes, "metrics.csv")

    assert preview.total_rows == 3
    assert preview.valid_rows_count == 1
    assert preview.duplicate_rows_count == 1
    assert preview.invalid_rows_count == 2  # Row 2 (duplicate) & Row 3 (bad phone)


def test_service_error_report_csv_injection_sanitization():
    """Verify formula injection characters are escaped in error reports."""
    errors = [
        {
            "row_number": 2,
            "register_number": "=2+5",
            "full_name": "@leak",
            "email": "-negative@mail.com",
            "error_message": "+dangerous_command",
            "is_duplicate": False
        }
    ]
    report = StudentCSVImportService.generate_error_report_csv(errors)
    assert "'=2+5" in report
    assert "'@leak" in report
    assert "'-negative@mail.com" in report
    assert "'+dangerous_command" in report
