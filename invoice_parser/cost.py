"""Estimate API cost from token counts."""

from decimal import Decimal

# USD per 1 million tokens (input, output).
# Haiku 5.5 rates apply to prompts up to 100k tokens; one invoice uses ~3k.
# Update these if Anthropic changes its pricing.
PRICES_PER_MILLION = {
    "claude-haiku-5-5": (Decimal("0.10"), Decimal("0.50")),
}

ONE_MILLION = Decimal("1000000")


def estimate_cost(input_tokens, output_tokens, model):
    """Return the estimated cost in USD as a Decimal, or None if the model has no price."""
    if model not in PRICES_PER_MILLION:
        return None
    input_price, output_price = PRICES_PER_MILLION[model]
    return (input_tokens * input_price + output_tokens * output_price) / ONE_MILLION