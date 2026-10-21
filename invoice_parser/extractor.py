"""Send one invoice file to Claude and return the extracted fields."""

import base64
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from invoice_parser.schema import INVOICE_TOOL, TOOL_NAME

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 2048

MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

SYSTEM_PROMPT = """You extract data from invoices and receipts.

Rules:
- Copy values exactly as printed. Never calculate, estimate or fill in a value
  that is not on the document; return null instead.
- Dates: convert to YYYY-MM-DD. Read the document's locale (e.g. 05/02/2026 on
  an Italian invoice is 2026-02-05).
- Numbers: return plain numbers without currency symbols or thousand
  separators (e.g. "1.012,60" becomes 1012.60).
- Discount: always a positive number.
- Tax: if there are several tax lines, return their sum.
- Line items: include every row of the items table, in order.
"""


@dataclass
class ExtractionResult:
    file: str
    data: dict
    input_tokens: int
    output_tokens: int
    model: str


def build_file_block(path: Path) -> dict:
    """Encode a PDF or image as a content block for the Messages API."""
    media_type = MEDIA_TYPES.get(path.suffix.lower())
    if media_type is None:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    encoded = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    block_type = "document" if media_type == "application/pdf" else "image"
    return {
        "type": block_type,
        "source": {"type": "base64", "media_type": media_type, "data": encoded},
    }


def extract_invoice(path, client=None, model=MODEL) -> ExtractionResult:
    """Extract structured invoice data from a single file."""
    path = Path(path)
    if client is None:
        load_dotenv()
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from .env

    # strict=True: the API guarantees the tool input matches the schema
    tool = {**INVOICE_TOOL, "strict": True}

    response = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        tools=[tool],
        tool_choice={"type": "tool", "name": TOOL_NAME},  # force this tool
        messages=[
            {
                "role": "user",
                "content": [
                    build_file_block(path),
                    {"type": "text", "text": "Extract the invoice data from this document."},
                ],
            }
        ],
    )

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:
        raise RuntimeError(
            f"No structured output for {path.name} (stop_reason={response.stop_reason})"
        )

    return ExtractionResult(
        file=path.name,
        data=tool_use.input,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        model=model,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m invoice_parser.extractor <file>")
        sys.exit(1)

    result = extract_invoice(sys.argv[1])
    print(json.dumps(result.data, indent=2, ensure_ascii=False))
    print(
        f"\nModel: {result.model} | "
        f"input tokens: {result.input_tokens} | output tokens: {result.output_tokens}"
    )