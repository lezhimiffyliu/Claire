"""
math_cleaner.py

Uses DeepSeek to clean up garbled LaTeX extracted from PDFs.
Run once after upload — results are stored back into the question bank.

Typical issues fixed:
  - Du f(-1,3) → $D_u f(-1,3)$
  - ∬ D f dA  → $\\iint_D f \\, dA$
  - fxy        → $f_{xy}$
  - 3/4        → $\frac{3}{4}$
  - Incomplete fragments reconstructed from context
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
    "If a problem is clearly incomplete or cut off, reconstruct it into a complete, "
    "solvable calculus problem based on the visible context (keep the same topic and numbers). "
    "Fix math notation and completeness. Do NOT change correct wording or problem structure. "
    "Do NOT add explanations or commentary."
)

_SEP = "\n<<<END>>>\n"


def _get_deepseek_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("DEEPSEEK_API_KEY", "")
        except Exception:
            pass
    return key


def clean_questions(questions: list["Question"], max_batch: int = 20) -> None:
    """
    In-place: rewrite question.text with clean LaTeX for up to max_batch questions.
    Uses DeepSeek (cheap) for math cleanup + fragment reconstruction.
    Silently skips if API is unavailable.
    """
    if not questions:
        return

    try:
        from openai import OpenAI

        api_key = _get_deepseek_key()
        if not api_key:
            return

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )

        batch = questions[:max_batch]

        # One request: all questions separated by <<<END>>>
        combined = _SEP.join(q.text for q in batch)
        prompt = (
            "Clean up the LaTeX and fix any incomplete fragments in each calculus "
            "problem below. "
            f"Problems are separated by '{_SEP.strip()}'. "
            "Return the cleaned problems in the same order, separated by the same "
            "delimiter. Do not add or remove problems.\n\n"
            + combined
        )

        resp = client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=4096,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )

        cleaned = resp.choices[0].message.content.split(_SEP)
        for q, new_text in zip(batch, cleaned):
            text = new_text.strip()
            if text:
                q.text = text

    except Exception:
        # Never crash the app — just skip cleaning
        pass
