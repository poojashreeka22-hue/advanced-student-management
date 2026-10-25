"""
Fee Invoices, Waivers, and Payments API Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.fee_service import FeeService
from app.schemas.fee import (
    FeeInvoiceCreate,
    FeeInvoiceResponse,
    FeePaymentCreate,
    FeePaymentResponse
)
from app.api.dependencies import get_current_user_optional
from app.models.user import User
from app.models.student import Student
from app.utils.calculations import calculate_fee_balance

router = APIRouter(prefix="/fees", tags=["Fees"])


@router.post("/invoices", response_model=FeeInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    data: FeeInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    service = FeeService(db)
    created_by = current_user.username if current_user else "bursar"
    inv = service.create_invoice(data, created_by=created_by)
    student = db.query(Student).filter(Student.id == inv.student_id).first()
    balance, _ = calculate_fee_balance(inv.amount, inv.waiver_amount, 0.0)
    return FeeInvoiceResponse(
        id=inv.id,
        invoice_number=inv.invoice_number,
        student_id=inv.student_id,
        academic_year=inv.academic_year,
        semester=inv.semester,
        title=inv.title,
        amount=inv.amount,
        waiver_amount=inv.waiver_amount,
        due_date=inv.due_date,
        status=inv.status,
        total_paid=0.0,
        balance_due=balance,
        created_at=inv.created_at,
        payments=[],
        student_name=student.full_name if student else None,
        student_reg=student.register_number if student else None
    )


@router.get("/invoices/student/{student_id}", response_model=List[FeeInvoiceResponse])
def get_student_invoices(student_id: int, db: Session = Depends(get_db)):
    service = FeeService(db)
    overview = service.get_student_fee_overview(student_id)
    student = db.query(Student).filter(Student.id == student_id).first()
    res = []
    for item in overview:
        inv = item["invoice"]
        payments_list = [
            FeePaymentResponse(
                id=p.id,
                invoice_id=p.invoice_id,
                payment_reference=p.payment_reference,
                amount_paid=p.amount_paid,
                payment_method=p.payment_method,
                payment_date=p.payment_date,
                recorded_by=p.recorded_by,
                notes=p.notes,
                created_at=p.created_at
            )
            for p in item["payments"]
        ]
        res.append(FeeInvoiceResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            student_id=inv.student_id,
            academic_year=inv.academic_year,
            semester=inv.semester,
            title=inv.title,
            amount=inv.amount,
            waiver_amount=inv.waiver_amount,
            due_date=inv.due_date,
            status=inv.status,
            total_paid=item["total_paid"],
            balance_due=item["balance_due"],
            created_at=inv.created_at,
            payments=payments_list,
            student_name=student.full_name if student else None,
            student_reg=student.register_number if student else None
        ))
    return res


@router.post("/payments", response_model=FeePaymentResponse, status_code=status.HTTP_201_CREATED)
def record_payment(
    data: FeePaymentCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    service = FeeService(db)
    recorded_by = current_user.username if current_user else "cashier"
    payment = service.record_payment(data, recorded_by=recorded_by)
    return FeePaymentResponse(
        id=payment.id,
        invoice_id=payment.invoice_id,
        payment_reference=payment.payment_reference,
        amount_paid=payment.amount_paid,
        payment_method=payment.payment_method,
        payment_date=payment.payment_date,
        recorded_by=payment.recorded_by,
        notes=payment.notes,
        created_at=payment.created_at
    )
