"""
Analytics and University Statistics API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    StatsResponse,
    DashboardMetrics,
    GradeDistributionItem,
    DepartmentPerformance
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Legacy statistics endpoint for general distribution metrics."""
    service = AnalyticsService(db)
    return service.get_legacy_stats()


@router.get("/metrics", response_model=DashboardMetrics)
def get_metrics(db: Session = Depends(get_db)):
    """Comprehensive real-time university dashboard indicators."""
    service = AnalyticsService(db)
    return service.get_dashboard_metrics()


@router.get("/grades", response_model=List[GradeDistributionItem])
def get_grade_distribution(db: Session = Depends(get_db)):
    """Grade breakdown across all examinations."""
    service = AnalyticsService(db)
    return service.get_grade_distribution()


@router.get("/departments", response_model=List[DepartmentPerformance])
def get_department_performance(db: Session = Depends(get_db)):
    """Department level student counts, average GPA, and attendance rates."""
    service = AnalyticsService(db)
    return service.get_department_performance()
