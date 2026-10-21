"""Check extracted invoice data and list the reasons it needs manual review."""

from decimal import Decimal, InvalidOperation

# Differences up to 1 cent are treated as rounding, not errors.
TOLERANCE = Decimal("0.01")
REQUIRED_FIELDS = ["vendor_name", "invoice_number", "invoice_date", "currency", "total"]


def to_decimal(value):
    """Convert a number from the API to Decimal. None (or junk) becomes None."""
    if value is None:
        return None
    try:
        # str() first: Decimal(0.1) would keep float noise, Decimal("0.1") does not.
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def validate(data):
    """Return a list of review reasons. An empty list means the invoice looks consistent."""
    reasons = []

    for field in REQUIRED_FIELDS:
        if data.get(field) in (None, ""):
            reasons.append(f"missing {field}")

    items = data.get("line_items") or []
    amounts = [to_decimal(item.get("amount")) for item in items]
    items_sum = None
    if not items:
        reasons.append("no line items")
    elif None in amounts:
        reasons.append("line item without amount")
    else:
        items_sum = sum(amounts, Decimal("0"))

    subtotal = to_decimal(data.get("subtotal"))
    discount = to_decimal(data.get("discount")) or Decimal("0")
    tax = to_decimal(data.get("tax")) or Decimal("0")
    total = to_decimal(data.get("total"))

    # Check 1: line items add up to the subtotal.
    if subtotal is not None and items_sum is not None and abs(items_sum - subtotal) > TOLERANCE:
        reasons.append(f"line items sum {items_sum} != subtotal {subtotal}")

    # Check 2: subtotal - discount + tax = total.
    # If the invoice has no subtotal, use the line items sum instead.
    base = subtotal if subtotal is not None else items_sum
    if base is not None and total is not None:
        expected = base - discount + tax
        if abs(expected - total) > TOLERANCE:
            label = "subtotal" if subtotal is not None else "line items sum"
            reasons.append(f"{label} - discount + tax = {expected} != total {total}")

    return reasons