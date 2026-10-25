"""
Analytics and Statistics schemas.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class StatsResponse(BaseModel):
    """Legacy and general statistics schema."""
    total_students: int
    department_counts: Dict[str, int]
    academic_year_counts: Dict[str, int]


class DashboardMetrics(BaseModel):
    total_students: int
    active_students: int
    total_courses: int
    total_faculty: int
    overall_attendance_rate: float
    total_fees_collected: float
    total_fees_outstanding: float
    department_distribution: Dict[str, int]
    academic_year_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    recent_admissions_count: int


class GradeDistributionItem(BaseModel):
    letter_grade: str
    count: int
    percentage: float


class DepartmentPerformance(BaseModel):
    department: str
    student_count: int
    average_gpa: float
    attendance_rate: float
