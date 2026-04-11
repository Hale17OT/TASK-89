"""
Pure-Python financial domain service.
No Django imports -- only stdlib.
"""
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP


def compute_order_total(line_items: list[dict]) -> dict:
    """
    Compute subtotal and total from a list of line-item dicts.

    Each item must have 'quantity' (int) and 'unit_price' (Decimal or str).
    Returns {'subtotal': Decimal, 'tax_amount': Decimal, 'total_amount': Decimal}.
    Tax is currently 0; the structure exists for future use.
    """
    subtotal = Decimal("0.00")
    for item in line_items:
        qty = int(item["quantity"])
        price = Decimal(str(item["unit_price"]))
        line_total = (price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal += line_total

    tax_amount = Decimal("0.00")
    total_amount = subtotal + tax_amount

    return {
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
    }


def validate_payment_amount(order, amount: Decimal) -> list[str]:
    """
    Validate that a payment amount does not exceed the remaining balance.

    Args:
        order: Order instance with total_amount and amount_paid attributes.
        amount: The payment amount to validate.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    amount = Decimal(str(amount))

    if amount <= Decimal("0.00"):
        errors.append("Payment amount must be greater than zero.")
        return errors

    remaining = order.total_amount - order.amount_paid
    if amount > remaining:
        errors.append(
            f"Payment amount {amount} exceeds remaining balance {remaining}."
        )

    return errors


def validate_refund_amount(order, amount: Decimal) -> list[str]:
    """
    Validate that a refund amount does not exceed the paid amount.

    Args:
        order: Order instance with amount_paid attribute.
        amount: The refund amount to validate.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    amount = Decimal(str(amount))

    if amount <= Decimal("0.00"):
        errors.append("Refund amount must be greater than zero.")
        return errors

    if amount > order.amount_paid:
        errors.append(
            f"Refund amount {amount} exceeds total paid amount {order.amount_paid}."
        )

    return errors


def generate_order_number() -> str:
    """
    Generate an order number in the format ORD-YYYYMMDD-NNNN.

    Sequential within the day, based on existing orders for today.
    This function must be called within a transaction that holds a
    lock on the Order table to avoid duplicates.
    """
    # Deferred import to keep this module pure-Python for unit testing.
    # The caller (serializer) is always in a Django context.
    from apps.financials.models import Order

    today = date.today()
    date_str = today.strftime("%Y%m%d")
    prefix = f"ORD-{date_str}-"

    last_order = (
        Order.objects.select_for_update()
        .filter(order_number__startswith=prefix)
        .order_by("-order_number")
        .first()
    )

    if last_order:
        last_seq = int(last_order.order_number.split("-")[-1])
        next_seq = last_seq + 1
    else:
        next_seq = 1

    return f"{prefix}{next_seq:04d}"
