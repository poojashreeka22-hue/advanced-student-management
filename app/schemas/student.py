"""
Student data validation and serialization schemas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class StudentBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of student")
    register_number: str = Field(..., min_length=2, max_length=50, description="Unique registration number")
    email: str = Field(..., min_length=5, max_length=100, description="Valid email address")
    phone_number: str = Field(..., min_length=7, max_length=20, description="Phone contact number")
    department: str = Field(..., min_length=2, max_length=100, description="Department name")
    academic_year: str = Field(..., min_length=2, max_length=50, description="Current academic year")

    # Extended profile attributes (optional on create, defaulted)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[str] = Field(None, max_length=20)
    gender: Optional[str] = Field(None, max_length=20)
    department_id: Optional[int] = None
    semester: int = Field(default=1, ge=1, le=8)
    status: str = Field(default="active", max_length=30)  # applicant, active, suspended, graduated, withdrawn
    admission_date: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    guardian_name: Optional[str] = Field(None, max_length=100)
    guardian_phone: Optional[str] = Field(None, max_length=20)
    gpa: float = Field(default=0.0, ge=0.0, le=10.0)

    @field_validator("full_name", "register_number", "department", "academic_year")
    @classmethod
    def strip_and_validate_non_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field must not be empty or whitespace only")
        return s

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        s = v.strip()
        if not EMAIL_REGEX.match(s):
            raise ValueError("Invalid email format (e.g. student@college.edu)")
        return s

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        s = v.strip()
        cleaned = re.sub(r"[\s\-\+\(\)]", "", s)
        if not cleaned.isdigit() or len(cleaned) < 7:
            raise ValueError("Phone number must contain at least 7 digits")
        return s


class StudentCreate(StudentBase):
    """Schema used when registering or admitting a new student."""
    pass


class StudentUpdate(BaseModel):
    """Schema used when updating an existing student's details."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    register_number: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=7, max_length=20)
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    academic_year: Optional[str] = Field(None, min_length=2, max_length=50)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    department_id: Optional[int] = None
    semester: Optional[int] = Field(None, ge=1, le=8)
    status: Optional[str] = None
    admission_date: Optional[str] = None
    address: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=10.0)

    @field_validator("full_name", "register_number", "department", "academic_year")
    @classmethod
    def strip_and_validate_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip()
            if not s:
                raise ValueError("Field must not be empty or whitespace only")
            return s
        return v

    @field_validator("email")
    @classmethod
    def validate_optional_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip()
            if not EMAIL_REGEX.match(s):
                raise ValueError("Invalid email format (e.g. student@college.edu)")
            return s
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_optional_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip()
            cleaned = re.sub(r"[\s\-\+\(\)]", "", s)
            if not cleaned.isdigit() or len(cleaned) < 7:
                raise ValueError("Phone number must contain at least 7 digits")
            return s
        return v


class StudentStatusUpdate(BaseModel):
    status: str = Field(..., description="applicant, active, suspended, graduated, withdrawn")
    reason: Optional[str] = None


class StudentResponse(StudentBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StudentDetailResponse(StudentResponse):
    """Deep profile response including academic records."""
    total_enrollments: int = 0
    attendance_rate: float = 0.0
    outstanding_fee_balance: float = 0.0


class StudentCSVRow(BaseModel):
    row_number: int
    register_number: str
    full_name: str
    email: str
    phone_number: str
    department: str
    academic_year: str
    semester: int = 1
    status: str = "active"
    gpa: float = 0.0
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    address: Optional[str] = None
    is_valid: bool = True
    is_duplicate: bool = False
    duplicate_reason: Optional[str] = None
    errors: List[str] = []


class StudentCSVImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    duplicate_rows_count: int
    preview_rows: List[StudentCSVRow]
    error_summary: List[Dict[str, Any]]


class StudentCSVImportResult(BaseModel):
    total_rows: int
    imported_count: int
    failed_count: int
    duplicate_count: int
    imported_students: List[StudentResponse] = []
    errors: List[Dict[str, Any]] = []


class StudentCSVErrorReportRequest(BaseModel):
    errors: List[Dict[str, Any]]


StudentCSVRow.model_rebuild()
StudentCSVImportPreviewResponse.model_rebuild()
StudentCSVImportResult.model_rebuild()
StudentCSVErrorReportRequest.model_rebuild()
