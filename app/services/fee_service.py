"""
Fee Ledger Domain Service: Invoicing, Payments, Waivers, and Overpayment Protection.
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.fee_repo import FeeRepository
from app.repositories.student_repo import StudentRepository
from app.repositories.audit_repo import AuditRepository
from app.models.fee import FeeInvoice, FeePayment
from app.schemas.fee import FeeInvoiceCreate, FeePaymentCreate, FeeInvoiceResponse, FeePaymentResponse
from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    InvalidPaymentException,
    ValidationException
)
from app.utils.calculations import calculate_fee_balance


class FeeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FeeRepository(db)
        self.student_repo = StudentRepository(db)
        self.audit_repo = AuditRepository(db)

    def create_invoice(
        self,
        data: FeeInvoiceCreate,
        created_by: Optional[str] = None
    ) -> FeeInvoice:
        student = self.student_repo.get(data.student_id)
        if not student:
            raise EntityNotFoundException("Student", data.student_id)

        if data.amount <= 0.0:
            raise ValidationException("Invoice amount must be strictly greater than zero.")

        if data.waiver_amount < 0.0 or data.waiver_amount > data.amount:
            raise ValidationException("Waiver/scholarship amount cannot be negative or exceed the total invoice amount.")

        # Generate unique invoice number
        inv_number = f"INV-{student.register_number}-{data.semester}-{uuid.uuid4().hex[:6].upper()}"

        balance, initial_status = calculate_fee_balance(data.amount, data.waiver_amount, 0.0)

        invoice = FeeInvoice(
            invoice_number=inv_number,
            student_id=data.student_id,
            academic_year=data.academic_year,
            semester=data.semester,
            title=data.title.strip(),
            amount=data.amount,
            waiver_amount=data.waiver_amount,
            due_date=data.due_date,
            status=initial_status
        )
        created = self.repo.create_invoice(invoice)

        self.audit_repo.log_event(
            action="FEE_INVOICE_CREATE",
            entity_type="FeeInvoice",
            entity_id=str(created.id),
            username=created_by,
            new_values=f"Invoice {created.invoice_number}, Student: {student.full_name}, Amount: {created.amount}, Waiver: {created.waiver_amount}"
        )
        return created

    def record_payment(
        self,
        data: FeePaymentCreate,
        recorded_by: Optional[str] = None
    ) -> FeePayment:
        invoice = self.repo.get_invoice(data.invoice_id)
        if not invoice:
            raise EntityNotFoundException("FeeInvoice", data.invoice_id)

        if data.amount_paid <= 0.0:
            raise InvalidPaymentException("Payment amount must be greater than zero.")

        # Calculate current balance
        payments = self.repo.get_payments_for_invoice(invoice.id)
        total_paid_so_far = sum(p.amount_paid for p in payments)
        balance_due, _ = calculate_fee_balance(invoice.amount, invoice.waiver_amount, total_paid_so_far)

        if balance_due <= 0.0:
            raise InvalidPaymentException("This invoice has already been fully paid. No further payments accepted.")

        # Prevent overpayment
        if round(data.amount_paid, 2) > round(balance_due, 2):
            raise InvalidPaymentException(
                f"Payment amount (${data.amount_paid:.2f}) exceeds outstanding balance (${balance_due:.2f})."
            )

        ref_number = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        payment = FeePayment(
            invoice_id=data.invoice_id,
            payment_reference=ref_number,
            amount_paid=data.amount_paid,
            payment_method=data.payment_method,
            payment_date=data.payment_date or "2026-10-25",
            recorded_by=recorded_by,
            notes=data.notes
        )
        created_payment = self.repo.create_payment(payment)

        # Update invoice status
        new_total_paid = total_paid_so_far + data.amount_paid
        new_balance, new_status = calculate_fee_balance(invoice.amount, invoice.waiver_amount, new_total_paid)
        invoice.status = new_status
        self.repo.update_invoice(invoice)

        self.audit_repo.log_event(
            action="FEE_PAYMENT",
            entity_type="FeePayment",
            entity_id=str(created_payment.id),
            username=recorded_by,
            new_values=f"Ref: {ref_number}, Paid: {data.amount_paid}, New Balance: {new_balance}, Status: {new_status}"
        )
        return created_payment

    def get_student_fee_overview(self, student_id: int) -> List[Dict[str, Any]]:
        invoices = self.repo.get_student_invoices(student_id)
        results = []
        for inv in invoices:
            payments = self.repo.get_payments_for_invoice(inv.id)
            total_paid = sum(p.amount_paid for p in payments)
            balance, status = calculate_fee_balance(inv.amount, inv.waiver_amount, total_paid)
            results.append({
                "invoice": inv,
                "total_paid": round(total_paid, 2),
                "balance_due": round(balance, 2),
                "payments": payments
            })
        return results
