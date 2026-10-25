"""
Schemas package exports.
"""

from .common import MessageResponse, PaginatedResponse
from .user import UserBase, UserCreate, UserUpdate, UserResponse, TokenResponse, LoginRequest
from .department import DepartmentBase, DepartmentCreate, DepartmentUpdate, DepartmentResponse
from .faculty import FacultyBase, FacultyCreate, FacultyUpdate, FacultyResponse
from .course import CourseBase, CourseCreate, CourseUpdate, CourseResponse
from .student import StudentBase, StudentCreate, StudentUpdate, StudentStatusUpdate, StudentResponse, StudentDetailResponse
from .enrollment import EnrollmentBase, EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse
from .attendance import AttendanceBase, AttendanceCreate, BulkAttendanceCreate, BulkAttendanceItem, AttendanceResponse, StudentAttendanceSummary
from .examination import ExaminationBase, ExaminationCreate, ExaminationUpdate, ExaminationResponse
from .grade import GradeEntryBase, GradeEntryCreate, GradeEntryUpdate, GradeEntryResponse, AcademicTranscript, AcademicTranscriptItem
from .fee import FeeInvoiceBase, FeeInvoiceCreate, FeeInvoiceUpdate, FeeInvoiceResponse, FeePaymentCreate, FeePaymentResponse
from .timetable import ClassroomBase, ClassroomCreate, ClassroomResponse, TimetableSlotBase, TimetableSlotCreate, TimetableSlotResponse, ConflictCheckResult
from .audit_log import AuditLogResponse
from .notification import NotificationCreate, NotificationResponse
from .analytics import StatsResponse, DashboardMetrics, GradeDistributionItem, DepartmentPerformance

__all__ = [
    "MessageResponse",
    "PaginatedResponse",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "TokenResponse",
    "LoginRequest",
    "DepartmentBase",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "FacultyBase",
    "FacultyCreate",
    "FacultyUpdate",
    "FacultyResponse",
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseResponse",
    "StudentBase",
    "StudentCreate",
    "StudentUpdate",
    "StudentStatusUpdate",
    "StudentResponse",
    "StudentDetailResponse",
    "EnrollmentBase",
    "EnrollmentCreate",
    "EnrollmentUpdate",
    "EnrollmentResponse",
    "AttendanceBase",
    "AttendanceCreate",
    "BulkAttendanceCreate",
    "BulkAttendanceItem",
    "AttendanceResponse",
    "StudentAttendanceSummary",
    "ExaminationBase",
    "ExaminationCreate",
    "ExaminationUpdate",
    "ExaminationResponse",
    "GradeEntryBase",
    "GradeEntryCreate",
    "GradeEntryUpdate",
    "GradeEntryResponse",
    "AcademicTranscript",
    "AcademicTranscriptItem",
    "FeeInvoiceBase",
    "FeeInvoiceCreate",
    "FeeInvoiceUpdate",
    "FeeInvoiceResponse",
    "FeePaymentCreate",
    "FeePaymentResponse",
    "ClassroomBase",
    "ClassroomCreate",
    "ClassroomResponse",
    "TimetableSlotBase",
    "TimetableSlotCreate",
    "TimetableSlotResponse",
    "ConflictCheckResult",
    "AuditLogResponse",
    "NotificationCreate",
    "NotificationResponse",
    "StatsResponse",
    "DashboardMetrics",
    "GradeDistributionItem",
    "DepartmentPerformance",
]
