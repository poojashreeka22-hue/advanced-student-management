"""
Department schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DepartmentBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    head_of_department: Optional[str] = Field(None, max_length=100)
    hod_faculty_id: Optional[int] = Field(None, description="Assigned Faculty ID of HOD")
    building: Optional[str] = Field(None, max_length=100)
    budget: float = Field(default=0.0, ge=0.0)
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    head_of_department: Optional[str] = Field(None, max_length=100)
    hod_faculty_id: Optional[int] = None
    building: Optional[str] = Field(None, max_length=100)
    budget: Optional[float] = Field(None, ge=0.0)
    is_active: Optional[bool] = None


class AssignHODRequest(BaseModel):
    faculty_id: int = Field(..., gt=0, description="Eligible faculty member ID to assign as HOD")


class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
