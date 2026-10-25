"""
Fee invoice, payment, and ledger schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class FeeInvoiceBase(BaseModel):
    student_id: int
    academic_year: str = Field(default="2026-2027")
    semester: int = Field(default=1, ge=1, le=8)
    title: str = Field(..., min_length=2, max_length=100)
    amount: float = Field(..., gt=0.0)
    waiver_amount: float = Field(default=0.0, ge=0.0)
    due_date: str = Field(..., description="YYYY-MM-DD")


class FeeInvoiceCreate(FeeInvoiceBase):
    pass


class FeeInvoiceUpdate(BaseModel):
    title: Optional[str] = None
    waiver_amount: Optional[float] = Field(None, ge=0.0)
    due_date: Optional[str] = None
    status: Optional[str] = None


class FeePaymentCreate(BaseModel):
    invoice_id: int
    amount_paid: float = Field(..., gt=0.0)
    payment_method: str = Field(default="bank_transfer")  # cash, card, bank_transfer, online
    payment_date: Optional[str] = None
    notes: Optional[str] = None


class FeePaymentResponse(BaseModel):
    id: int
    invoice_id: int
    payment_reference: str
    amount_paid: float
    payment_method: str
    payment_date: str
    recorded_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeeInvoiceResponse(FeeInvoiceBase):
    id: int
    invoice_number: str
    status: str
    total_paid: float = 0.0
    balance_due: float = 0.0
    created_at: datetime
    payments: List[FeePaymentResponse] = []
    student_name: Optional[str] = None
    student_reg: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
