"""
Reports and CSV Export API Endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.export_service import ExportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/export/students")
def export_students(
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Export student roster as safe CSV with formula injection sanitization."""
    service = ExportService(db)
    csv_content = service.export_students_csv(department=department)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students_export.csv"}
    )


@router.get("/export/fees")
def export_fees(db: Session = Depends(get_db)):
    """Export fee ledger as safe CSV."""
    service = ExportService(db)
    csv_content = service.export_fees_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fees_export.csv"}
    )
