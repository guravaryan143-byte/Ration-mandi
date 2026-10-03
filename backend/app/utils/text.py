from __future__ import annotations

import re


def normalize_name(value: str) -> str:
    """Lower-case, trim and collapse whitespace so 'Paracetamol  500MG' matches 'paracetamol 500mg'."""
    return re.sub(r"\s+", " ", value.strip().lower())
