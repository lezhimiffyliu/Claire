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
    "You are a LaTeX math formatter and exam text cleaner. "
    "You receive calculus problem text extracted from a PDF exam. "
    "The text may have several issues — fix ALL of them:\n"
    "1. STRIP embedded multiple-choice answer options. "
    "   These look like 'A 9 B 9√2 C −9 D -9 E None of the above' "
    "   or '(A) ... (B) ... (C) ...' — remove them entirely.\n"
    "2. STRIP page metadata: course names, instructor names, page numbers, "
    "   semester labels (e.g. 'Fall 2017 Calculus III Corrin Clarkson Page 3 of 12'). "
    "   Remove anything that is clearly footer/header info, not part of the problem.\n"
    "3. FIX garbled LaTeX math: subscripts inline (fxy → $f_{xy}$), "
    "   missing limits on integrals, fractions written as a/b, "
    "   square roots written as sqrt or √, superscripts like y3 → $y^3$, etc. "
    "   Rewrite math inside $...$ (inline) or $$...$$ (display).\n"
    "4. If a problem is incomplete or cut off after cleaning, reconstruct it into "
    "   a complete solvable calculus problem using the visible context and numbers.\n"
    "Return ONLY the clean problem statement. No explanations, no commentary."
)

_SEP = "\n<<<END>>>\n"

import re as _re

def _pre_strip(text: str) -> str:
    """
    Quick regex pass to remove obvious MC answer options and page metadata
    before sending to DeepSeek.
    """
    # 1a. Strip inline MC after "?" — e.g. "...point? A 9 B 9√2 C −9 D -9 E ..."
    text = _re.sub(r'(\?)\s*[A-Ea-e][\s.)].+$', r'\1', text, flags=_re.DOTALL)
    # 1b. Strip inline "(A) ... (B) ..." after a sentence-ending period
    text = _re.sub(r'([.!])\s*\([A-Ea-e]\)\s+.+$', r'\1', text, flags=_re.DOTALL)

    # 2. Strip MC options on their own lines — handles "(A) ...", "A) ...", "A. ..."
    text = _re.sub(r'^\s*\(?[A-Ea-e]\)?[.)]\s+.+$', '', text, flags=_re.MULTILINE)

    # 3. Strip "None / All of the above"
    text = _re.sub(r'\b(None|All)\s+of\s+the\s+above\b', '', text, flags=_re.IGNORECASE)

    # 4. Strip page footer "Page X of Y"
    text = _re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=_re.IGNORECASE)

    # 5. Strip semester + course + instructor footer line
    #    e.g. "Fall 2017 Calculus III (Math 123 Sec. 004) Corrin Clarkson Page 3 of 12"
    text = _re.sub(
        r'(Fall|Spring|Summer|Winter)\s+\d{4}[^\n]*',
        '', text, flags=_re.IGNORECASE,
    )

    # 6. Strip standalone "Math NNN Sec. NNN" metadata
    text = _re.sub(r'Math\s+\d+\s+Sec\.?\s*\d+[^\n]*', '', text, flags=_re.IGNORECASE)

    # Collapse excess whitespace
    text = _re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


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

        # Pre-strip obvious MC options and page metadata before sending to model
        pre_cleaned = [_pre_strip(q.text) for q in batch]

        # One request: all questions separated by <<<END>>>
        combined = _SEP.join(pre_cleaned)
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
