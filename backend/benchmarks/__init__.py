"""
Claire Benchmark Suite

Offline evaluation tooling. Two independent surfaces live here:

- ``evaluator.py`` — SymPy answer-equivalence checking (``evaluate``,
  ``is_correct``). This is the ground-truth leak/answer comparator reused by the
  teaching-trajectory harness.
- ``teaching_eval/`` — the teaching-trajectory evaluation harness (Milestone A):
  drives the real ``claire_core`` loop with a simulated student and scores each
  trajectory (leak check + structural invariants + LLM-as-judge rubric).

Only the stable, existing symbols are re-exported at package level so importing
any submodule (e.g. ``benchmarks.teaching_eval.runner``) never fails.
"""
from .evaluator import (
    EvalResult,
    batch_evaluate,
    evaluate,
    is_correct,
)

__all__ = [
    "EvalResult",
    "evaluate",
    "is_correct",
    "batch_evaluate",
]
