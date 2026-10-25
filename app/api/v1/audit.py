"""
Audit Log API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.audit_repo import AuditRepository
from app.schemas.audit_log import AuditLogResponse
from app.api.dependencies import require_roles
from app.core.permissions import Role

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve recent administrative audit logs."""
    repo = AuditRepository(db)
    return repo.get_recent(limit=limit)
