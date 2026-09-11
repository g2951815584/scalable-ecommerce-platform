"""Core unit tests for payment-service."""

from app.models import Payment, PaymentTransaction, Refund


def test_payment_refundable_derivation():
    payment = Payment(id=1, payment_no="PA1", order_no="SO1", user_id=1,
                      channel="STRIPE", amount_cents=19900, currency="CNY",
                      refunded_amount_cents=5000, expires_at=None)
    assert payment.amount_cents - payment.refunded_amount_cents == 14900


def test_transaction_direction():
    txn = PaymentTransaction(id=1, transaction_no="TX1", transaction_type="PAYMENT",
                             payment_no="PA1", order_no="SO1", user_id=1,
                             channel="STRIPE", direction="IN", amount_cents=19900,
                             transaction_at=None)
    assert txn.direction == "IN"
    assert txn.transaction_type == "PAYMENT"


def test_refund_type_full_check():
    refund = Refund(id=1, refund_no="RF1", payment_no="PA1", order_no="SO1", user_id=1,
                    channel="STRIPE", refund_type="FULL", amount_cents=19900,
                    payment_amount_cents=19900, reason="退款", idempotency_key="rk")
    assert refund.refund_type == "FULL"