"""
Student Management and Admissions API Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.student_service import StudentService
from app.services.grade_service import GradeService
from app.services.student_import_service import StudentCSVImportService
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentStatusUpdate,
    StudentResponse,
    StudentDetailResponse,
    StudentCSVImportPreviewResponse,
    StudentCSVImportResult,
    StudentCSVErrorReportRequest
)
from app.schemas.grade import AcademicTranscript
from app.schemas.common import MessageResponse
from app.api.dependencies import get_current_user_optional, require_roles
from app.models.user import User
from app.core.permissions import Role

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    student_in: StudentCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Register / admit a new student into the university."""
    service = StudentService(db)
    username = current_user.username if current_user else "anonymous"
    return service.create_student(student_in, current_username=username)


@router.get("", response_model=List[StudentResponse])
def get_students(
    search: Optional[str] = Query(None, description="Search by name, register number, or email"),
    department: Optional[str] = Query(None, description="Filter by department"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    status: Optional[str] = Query(None, description="Filter by status (active, applicant, etc.)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("id"),
    sort_desc: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Retrieve students directory with search, filtering, and pagination."""
    service = StudentService(db)
    items, _ = service.search_students(
        search=search,
        department=department,
        academic_year=academic_year,
        status=status,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_desc=sort_desc
    )
    return items


@router.get("/csv-template")
def download_csv_template():
    """Download RFC 4180 CSV template for bulk student admission."""
    template_content = StudentCSVImportService.get_csv_template()
    return Response(
        content=template_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=student_import_template.csv"}
    )


@router.post("/import-csv/preview", response_model=StudentCSVImportPreviewResponse)
async def preview_csv_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([Role.ADMIN.value]))
):
    """Validate uploaded CSV file and return pre-import inspection results."""
    file_bytes = await file.read()
    service = StudentCSVImportService(db)
    return service.preview_import(file_bytes, filename=file.filename or "upload.csv")


@router.post("/import-csv", response_model=StudentCSVImportResult)
async def import_students_csv(
    file: UploadFile = File(...),
    allow_partial: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([Role.ADMIN.value]))
):
    """Bulk import student records from an uploaded CSV file with transaction safety."""
    file_bytes = await file.read()
    service = StudentCSVImportService(db)
    return service.import_students_from_csv(
        file_bytes=file_bytes,
        filename=file.filename or "upload.csv",
        allow_partial=allow_partial,
        current_username=current_user.username
    )


@router.post("/import-csv/error-report")
def download_error_report(
    error_data: StudentCSVErrorReportRequest,
    current_user: User = Depends(require_roles([Role.ADMIN.value]))
):
    """Download formula-injection safe CSV report of rejected rows."""
    report_csv = StudentCSVImportService.generate_error_report_csv(error_data.errors)
    return Response(
        content=report_csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=student_import_errors.csv"}
    )


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Retrieve a single student by identifier."""
    service = StudentService(db)
    return service.get_student(student_id)


@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    student_in: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Update student record fields."""
    service = StudentService(db)
    username = current_user.username if current_user else "anonymous"
    return service.update_student(student_id, student_in, current_username=username)


@router.patch("/{student_id}/status", response_model=StudentResponse)
def update_student_status(
    student_id: int,
    status_in: StudentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Change student status (applicant, active, suspended, graduated, withdrawn)."""
    service = StudentService(db)
    username = current_user.username if current_user else "anonymous"
    return service.update_status(
        student_id,
        new_status=status_in.status,
        reason=status_in.reason,
        current_username=username
    )


@router.delete("/{student_id}", response_model=MessageResponse)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Permanently delete a student record."""
    service = StudentService(db)
    username = current_user.username if current_user else "anonymous"
    service.delete_student(student_id, current_username=username)
    return MessageResponse(message="Student deleted successfully")


@router.get("/{student_id}/dossier", response_model=StudentDetailResponse)
def get_student_dossier(student_id: int, db: Session = Depends(get_db)):
    """Retrieve advanced student dossier with attendance, fees, and enrollment statistics."""
    service = StudentService(db)
    dossier = service.get_student_dossier(student_id)
    student = dossier["student"]
    return StudentDetailResponse(
        id=student.id,
        full_name=student.full_name,
        register_number=student.register_number,
        email=student.email,
        phone_number=student.phone_number,
        department=student.department,
        academic_year=student.academic_year,
        first_name=student.first_name,
        last_name=student.last_name,
        date_of_birth=student.date_of_birth,
        gender=student.gender,
        department_id=student.department_id,
        semester=student.semester,
        status=student.status,
        admission_date=student.admission_date,
        address=student.address,
        guardian_name=student.guardian_name,
        guardian_phone=student.guardian_phone,
        gpa=student.gpa,
        created_at=student.created_at,
        total_enrollments=dossier["total_enrollments"],
        attendance_rate=dossier["attendance_rate"],
        outstanding_fee_balance=dossier["outstanding_fee_balance"]
    )


@router.get("/{student_id}/transcript", response_model=AcademicTranscript)
def get_student_transcript(student_id: int, db: Session = Depends(get_db)):
    """Generate academic transcript with calculated GPA and grade breakdown."""
    grade_service = GradeService(db)
    return grade_service.generate_student_transcript(student_id)
