"""Tests for the validator, using fictional data only (no API calls)."""

from invoice_parser.validator import validate


def make_invoice(**overrides):
    """A fictional invoice whose totals add up: 3150 - 315 + 226.80 = 3061.80."""
    data = {
        "vendor_name": "Blue Pine Studio",
        "invoice_number": "BP-1001",
        "invoice_date": "2026-03-10",
        "due_date": "2026-04-09",
        "currency": "USD",
        "line_items": [
            {"description": "Design", "quantity": 10, "unit_price": 150, "amount": 1500},
            {"description": "Development", "quantity": 15, "unit_price": 110, "amount": 1650},
        ],
        "subtotal": 3150,
        "discount": 315,
        "tax": 226.80,
        "total": 3061.80,
    }
    data.update(overrides)
    return data


def test_consistent_invoice_has_no_reasons():
    assert validate(make_invoice()) == []


def test_wrong_total_is_flagged():
    reasons = validate(make_invoice(total=3100))
    assert len(reasons) == 1
    assert "!= total" in reasons[0]


def test_items_not_matching_subtotal_is_flagged():
    reasons = validate(make_invoice(subtotal=3000, total=2911.80))
    assert any("!= subtotal" in r for r in reasons)


def test_missing_subtotal_uses_line_items_sum():
    assert validate(make_invoice(subtotal=None)) == []


def test_missing_required_fields_are_flagged():
    reasons = validate(make_invoice(invoice_number=None, total=None))
    assert "missing invoice_number" in reasons
    assert "missing total" in reasons


def test_no_line_items_is_flagged():
    reasons = validate(make_invoice(line_items=[]))
    assert "no line items" in reasons