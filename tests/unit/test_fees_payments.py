"""
Automated Unit Tests: Fee Invoices, Waivers, Payments, and Overpayment Protection (100 cases).
"""

import pytest
from app.utils.calculations import calculate_fee_balance
from app.services.fee_service import FeeService
from app.schemas.fee import FeeInvoiceCreate, FeePaymentCreate
from app.core.exceptions import InvalidPaymentException, ValidationException


# ============================================================================
# 1. Fee Balance and Status Calculations (40 cases)
# ============================================================================
fee_cases = []
for i in range(1, 41):
    amount = 1000.0 + (i * 50)
    waiver = i * 10.0
    paid = (i * 20.0)
    net = max(0.0, amount - waiver)
    expected_balance = round(max(0.0, net - paid), 2)
    expected_status = "paid" if expected_balance == 0 else ("partial" if paid > 0 else "pending")
    fee_cases.append((amount, waiver, paid, expected_balance, expected_status))

@pytest.mark.parametrize("amount,waiver,paid,expected_balance,expected_status", fee_cases, ids=[f"fee_bal_{i}" for i in range(40)])
def test_fee_balance_formula(amount, waiver, paid, expected_balance, expected_status):
    balance, status = calculate_fee_balance(amount, waiver, paid)
    assert balance == expected_balance
    assert status == expected_status


# ============================================================================
# 2. Overpayment Prevention Enforcement (30 cases)
# ============================================================================
overpay_cases = []
for i in range(1, 31):
    # Invoice = 1000, Overpayment amount = 1000.01 + i
    overpay_cases.append((1000.0, 0.0, 1000.0 + (i * 1.5)))

@pytest.mark.parametrize("inv_amount,waiver,attempted_payment", overpay_cases, ids=[f"overpay_{i}" for i in range(30)])
def test_overpayment_rejection(db_session, sample_student, inv_amount, waiver, attempted_payment):
    fee_service = FeeService(db_session)
    invoice = fee_service.create_invoice(FeeInvoiceCreate(
        student_id=sample_student.id,
        title=f"Tuition Fee Overpay Test {attempted_payment}",
        amount=inv_amount,
        waiver_amount=waiver,
        due_date="2026-12-31"
    ))

    # Reject payment exceeding outstanding balance
    with pytest.raises(InvalidPaymentException):
        fee_service.record_payment(FeePaymentCreate(
            invoice_id=invoice.id,
            amount_paid=attempted_payment,
            payment_method="bank_transfer"
        ))


# ============================================================================
# 3. Partial Payment and Status Transitions (30 cases)
# ============================================================================
partial_payment_cases = [(1000.0, (i * 25.0)) for i in range(1, 31)]

@pytest.mark.parametrize("total_amount,first_payment", partial_payment_cases, ids=[f"partial_pay_{i}" for i in range(30)])
def test_partial_payment_lifecycle(db_session, sample_student, total_amount, first_payment):
    fee_service = FeeService(db_session)
    invoice = fee_service.create_invoice(FeeInvoiceCreate(
        student_id=sample_student.id,
        title=f"Tuition Lifecycle {first_payment}",
        amount=total_amount,
        waiver_amount=0.0,
        due_date="2026-12-31"
    ))
    assert invoice.status == "pending"

    # Make partial payment
    pay = fee_service.record_payment(FeePaymentCreate(
        invoice_id=invoice.id,
        amount_paid=first_payment,
        payment_method="bank_transfer"
    ))
    assert pay.amount_paid == first_payment

    # Refresh invoice status
    inv_updated = fee_service.repo.get_invoice(invoice.id)
    assert inv_updated.status in ("partial", "paid")
