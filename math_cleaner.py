"""
math_cleaner.py

Uses Claude Haiku to clean up garbled LaTeX extracted from PDFs.
Run once after upload — results are stored back into the question bank.

Typical issues fixed:
  - Du f(-1,3) → $D_u f(-1,3)$
  - ∬ D f dA  → $\iint_D f \, dA$
  - fxy        → $f_{xy}$
  - 3/4        → $\frac{3}{4}$
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from question_bank import Question

_SYSTEM = (
    "You are a LaTeX math formatter. You receive calculus problem text extracted "
    "from a PDF, where math notation may be garbled: subscripts appear inline, "
    "integral signs lose their limits, fractions are written a/b, etc. "
    "Rewrite each problem with correct LaTeX inside $...$ (inline) or $$...$$ (display). "
    "Fix ONLY math notation. Do NOT change wording, punctuation, or problem structure. "
    "Do NOT add explanations."
)

_SEP = "\n<<<END>>>\n"


def clean_questions(questions: list["Question"], max_batch: int = 20) -> None:
    """
    In-place: rewrite question.text with clean LaTeX for up to max_batch questions.
    Silently skips if Anthropic API is unavailable.
    """
    if not questions:
        return

    try:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        # Also try streamlit secrets
        if not api_key:
            try:
                import streamlit as st
                api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
            except Exception:
                pass
        if not api_key:
            return

        client = anthropic.Anthropic(api_key=api_key)
        batch = questions[:max_batch]

        # Build one prompt with all questions separated by <<<END>>>
        combined = _SEP.join(q.text for q in batch)
        prompt = (
            "Clean up the LaTeX in each calculus problem below. "
            f"Problems are separated by '{_SEP.strip()}'. "
            "Return the cleaned problems in the same order, separated by the same delimiter. "
            "Do not add or remove problems.\n\n"
            + combined
        )

        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=4096,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        cleaned = resp.content[0].text.split(_SEP)
        for q, new_text in zip(batch, cleaned):
            text = new_text.strip()
            if text:
                q.text = text

    except Exception:
        # Never crash the app — just skip cleaning
        pass
