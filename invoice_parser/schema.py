"""JSON schema for invoice extraction, sent to Claude as a tool definition.

The model is forced to call this tool, so its arguments always follow
the schema below. Fields are nullable: if a value is not on the document,
the model must return null instead of guessing.
"""

TOOL_NAME = "record_invoice"

LINE_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {
            "type": "string",
            "description": "Item or service description as written on the document.",
        },
        "quantity": {
            "type": ["number", "null"],
            "description": "Quantity. Null if not shown.",
        },
        "unit_price": {
            "type": ["number", "null"],
            "description": "Price per unit. Null if not shown.",
        },
        "amount": {
            "type": ["number", "null"],
            "description": "Line total (quantity x unit price). Null if not shown.",
        },
    },
    "required": ["description", "quantity", "unit_price", "amount"],
    "additionalProperties": False,
}

INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor_name": {
            "type": ["string", "null"],
            "description": "Name of the company that issued the invoice or receipt.",
        },
        "invoice_number": {
            "type": ["string", "null"],
            "description": "Invoice or receipt number exactly as printed.",
        },
        "invoice_date": {
            "type": ["string", "null"],
            "description": "Issue date in ISO format YYYY-MM-DD.",
        },
        "currency": {
            "type": ["string", "null"],
            "description": "ISO 4217 code (e.g. USD, EUR, BRL). Infer from symbol only if unambiguous.",
        },
        "line_items": {
            "type": "array",
            "items": LINE_ITEM_SCHEMA,
            "description": "All line items in the order they appear.",
        },
        "subtotal": {
            "type": ["number", "null"],
            "description": "Total before tax. Null if not shown.",
        },
        "tax": {
            "type": ["number", "null"],
            "description": "Sum of all taxes (VAT, sales tax, etc.). Null if not shown.",
        },
        "total": {
            "type": ["number", "null"],
            "description": "Final amount due, including tax.",
        },
    },
    "required": [
        "vendor_name",
        "invoice_number",
        "invoice_date",
        "currency",
        "line_items",
        "subtotal",
        "tax",
        "total",
    ],
    "additionalProperties": False,
}

INVOICE_TOOL = {
    "name": TOOL_NAME,
    "description": "Record the structured data extracted from an invoice or receipt.",
    "input_schema": INVOICE_SCHEMA,
}