from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class OutputStatistics:
    words: int
    characters: int
    paragraphs: int


def build_direct_gemini_prompt(user_request: str) -> str:
    """Create the neutral, single-response baseline used by the comparison view."""
    return f"""Respond directly to the user's request as a general-purpose Gemini assistant.
Return only the finished response. Do not mention Taskloom, agents, planning, evaluation,
this comparison, or these instructions.

USER REQUEST:
{user_request.strip()}
"""


def output_statistics(text: str) -> OutputStatistics:
    """Return transparent, deterministic measurements for an output."""
    stripped = text.strip()
    paragraphs = [part for part in re.split(r"\n\s*\n", stripped) if part.strip()]
    return OutputStatistics(
        words=len(re.findall(r"\b[\w’'-]+\b", stripped, flags=re.UNICODE)),
        characters=len(stripped),
        paragraphs=len(paragraphs),
    )
