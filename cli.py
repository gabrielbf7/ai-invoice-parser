"""Command-line entry point: python cli.py samples/"""

import argparse
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from invoice_parser.cost import estimate_cost
from invoice_parser.exporter import export_excel
from invoice_parser.extractor import extract_invoice
from invoice_parser.validator import validate

SUPPORTED = {".pdf", ".jpg", ".jpeg", ".png"}


def find_files(folder):
    """Return supported files in the folder, sorted by name."""
    files = Path(folder).iterdir()
    return sorted(p for p in files if p.suffix.lower() in SUPPORTED)


def main():
    parser = argparse.ArgumentParser(
        description="Extract invoice data with Claude and export to Excel."
    )
    parser.add_argument(
        "folder", help="folder with PDF, JPG or PNG invoices"
    )
    parser.add_argument(
        "--output", help="path of the .xlsx file (default: output/)"
    )
    args = parser.parse_args()

    files = find_files(args.folder)
    if not files:
        print(f"No PDF, JPG or PNG files found in {args.folder}")
        return

    load_dotenv()
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from .env

    records = []
    total_in = 0
    total_out = 0
    total_cost = Decimal("0")
    cost_known = True

    for i, path in enumerate(files, start=1):
        print(f"[{i}/{len(files)}] {path.name} ... ", end="", flush=True)
        try:
            result = extract_invoice(path, client=client)
        except Exception as exc:  # one bad file should not stop the batch
            records.append({
                "file": path.name,
                "data": None,
                "reasons": [f"extraction failed: {exc}"],
            })
            print("FAILED")
            continue

        reasons = validate(result.data)
        records.append({
            "file": path.name,
            "data": result.data,
            "reasons": reasons,
        })

        total_in += result.input_tokens
        total_out += result.output_tokens
        cost = estimate_cost(
            result.input_tokens, result.output_tokens, result.model
        )
        if cost is None:
            cost_known = False
        else:
            total_cost += cost

        if reasons:
            print(f"needs review ({len(reasons)} issue(s))")
        else:
            print("OK")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = args.output or f"output/invoices_{timestamp}.xlsx"
    saved = export_excel(records, output)

    review = sum(1 for r in records if r["reasons"])
    ok = len(records) - review
    print()
    print(f"Files processed: {len(records)} | OK: {ok} | Needs review: {review}")
    print(f"Tokens: {total_in:,} input / {total_out:,} output")
    if cost_known:
        print(f"Estimated API cost: US$ {total_cost:.4f}")
    else:
        print("Estimated API cost: unknown model price")
    print(f"Excel saved to: {saved}")


if __name__ == "__main__":
    main()