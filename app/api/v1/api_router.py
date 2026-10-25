"""
API v1 Router aggregation.
"""

from fastapi import APIRouter
from .authentication import router as auth_router
from .students import router as students_router
from .departments import router as departments_router
from .courses import router as courses_router
from .faculty import router as faculty_router
from .enrollments import router as enrollments_router
from .attendance import router as attendance_router
from .examinations import router as examinations_router
from .grades import router as grades_router
from .fees import router as fees_router
from .timetable import router as timetable_router
from .notifications import router as notifications_router
from .reports import router as reports_router
from .analytics import router as analytics_router
from .audit import router as audit_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(departments_router)
api_router.include_router(courses_router)
api_router.include_router(faculty_router)
api_router.include_router(enrollments_router)
api_router.include_router(attendance_router)
api_router.include_router(examinations_router)
api_router.include_router(grades_router)
api_router.include_router(fees_router)
api_router.include_router(timetable_router)
api_router.include_router(notifications_router)
api_router.include_router(reports_router)
api_router.include_router(analytics_router)
api_router.include_router(audit_router)
