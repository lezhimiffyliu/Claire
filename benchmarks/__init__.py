"""
Claire Benchmark Suite

Tools for evaluating Claire's calculus capabilities:
- evaluator.py: Core evaluation logic with SymPy equivalence checking
- run_benchmark.py: Run benchmark on Claire
- compare_models.py: Compare Claire vs GPT/other models
- download_math_dataset.py: Download MATH dataset for testing
"""

from .evaluator import (
    MathEvaluator,
    AnswerExtractor,
    BenchmarkRunner,
    EvalResult,
    BenchmarkResult,
)

__all__ = [
    'MathEvaluator',
    'AnswerExtractor',
    'BenchmarkRunner',
    'EvalResult',
    'BenchmarkResult',
]
