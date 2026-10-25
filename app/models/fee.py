"""
Fee invoice and payment models.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base


class FeeInvoice(Base):
    __tablename__ = "fee_invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year = Column(String(20), nullable=False)
    semester = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    waiver_amount = Column(Float, default=0.0, nullable=False)
    due_date = Column(String(20), nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, partial, paid, overdue, cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_rel = relationship("Student", back_populates="invoices")
    payments = relationship("FeePayment", back_populates="invoice_rel", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FeeInvoice(invoice_no='{self.invoice_number}', amount={self.amount}, status='{self.status}')>"


class FeePayment(Base):
    __tablename__ = "fee_payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("fee_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_reference = Column(String(50), unique=True, nullable=False, index=True)
    amount_paid = Column(Float, nullable=False)
    payment_method = Column(String(50), default="bank_transfer", nullable=False)  # cash, card, bank_transfer, online
    payment_date = Column(String(20), nullable=False)
    recorded_by = Column(String(100), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    invoice_rel = relationship("FeeInvoice", back_populates="payments")

    def __repr__(self) -> str:
        return f"<FeePayment(ref='{self.payment_reference}', amount={self.amount_paid})>"
