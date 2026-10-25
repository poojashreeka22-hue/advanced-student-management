"""
Fee invoices and payments repository.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.fee import FeeInvoice, FeePayment
from .base import BaseRepository


class FeeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_invoice(self, invoice_id: int) -> Optional[FeeInvoice]:
        return self.db.query(FeeInvoice).filter(FeeInvoice.id == invoice_id).first()

    def get_invoice_by_number(self, invoice_number: str) -> Optional[FeeInvoice]:
        return self.db.query(FeeInvoice).filter(
            func.lower(FeeInvoice.invoice_number) == invoice_number.strip().lower()
        ).first()

    def get_student_invoices(self, student_id: int) -> List[FeeInvoice]:
        return self.db.query(FeeInvoice).filter(FeeInvoice.student_id == student_id).all()

    def create_invoice(self, invoice: FeeInvoice) -> FeeInvoice:
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def update_invoice(self, invoice: FeeInvoice) -> FeeInvoice:
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def create_payment(self, payment: FeePayment) -> FeePayment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_payments_for_invoice(self, invoice_id: int) -> List[FeePayment]:
        return self.db.query(FeePayment).filter(FeePayment.invoice_id == invoice_id).all()
