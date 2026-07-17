"""AI rename suggestions — pure Python, no Qt."""
from __future__ import annotations

import json


def suggest_renames(names: list[str], provider: object) -> list[str | None]:
    """Ask AI for rename suggestions. Returns list same length as names, None=keep."""
    if not getattr(provider, "available", False) or not names:
        return [None] * len(names)

    prompt = (
        "Suggest better, more descriptive filenames for these files.\n"
        "Return a JSON array of strings, same length as input.\n"
        "Use null to keep the original name.\n"
        f"Input: {json.dumps(names)}\n"
        "Return ONLY the JSON array."
    )
    response = provider.chat([{"role": "user", "content": prompt}])  # type: ignore[union-attr]
    try:
        result = json.loads(response.strip())
        if not isinstance(result, list):
            return [None] * len(names)
        while len(result) < len(names):
            result.append(None)
        return result[: len(names)]
    except (json.JSONDecodeError, TypeError):
        return [None] * len(names)
