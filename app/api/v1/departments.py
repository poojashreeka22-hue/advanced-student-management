"""
Department API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.academic_service import AcademicService
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    AssignHODRequest
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(dept_in: DepartmentCreate, db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.create_department(dept_in)


@router.get("", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.get_all_departments()


@router.get("/{dept_id}", response_model=DepartmentResponse)
def get_department(dept_id: int, db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.get_department(dept_id)


@router.put("/{dept_id}", response_model=DepartmentResponse)
def update_department(dept_id: int, dept_in: DepartmentUpdate, db: Session = Depends(get_db)):
    service = AcademicService(db)
    return service.update_department(dept_id, dept_in)


@router.post("/{dept_id}/hod", response_model=DepartmentResponse)
def assign_head_of_department(
    dept_id: int,
    request: AssignHODRequest,
    db: Session = Depends(get_db)
):
    """Assign an eligible faculty member as Head of Department."""
    service = AcademicService(db)
    return service.assign_hod(dept_id, request.faculty_id)


@router.delete("/{dept_id}/hod", response_model=DepartmentResponse)
def vacate_head_of_department(dept_id: int, db: Session = Depends(get_db)):
    """Vacate the Head of Department position for a department."""
    service = AcademicService(db)
    return service.vacate_hod(dept_id)


@router.delete("/{dept_id}", response_model=MessageResponse)
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    """Safely delete department with dependent records verification."""
    service = AcademicService(db)
    service.delete_department(dept_id)
    return MessageResponse(message=f"Department #{dept_id} successfully deleted.")
