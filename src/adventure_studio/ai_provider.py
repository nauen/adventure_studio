"""Opt-in OpenAI adapter; the deterministic story core never imports an SDK."""

from __future__ import annotations

import os


def generate_openai_operations(system: str, user: str) -> str:
    """Call the Responses API only when the author explicitly requests it."""
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY ist nicht gesetzt; die KI-Anbindung ist optional")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ValueError("OpenAI-SDK fehlt: pip install -e '.[ai]'") from exc

    client = OpenAI(timeout=45.0, max_retries=1)
    response = client.responses.create(
        model=os.environ.get("ADVENTURE_STUDIO_AI_MODEL", "gpt-4.1-mini"),
        store=False,
        input=[{"role": "developer", "content": system},
               {"role": "user", "content": user}],
        text={"format": {"type": "json_object"}},
    )
    if not response.output_text:
        raise ValueError("Die KI hat keinen JSON-Vorschlag zurückgegeben")
    return response.output_text
