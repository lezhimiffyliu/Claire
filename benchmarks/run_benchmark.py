#!/usr/bin/env python3
"""
Run benchmark evaluation on Claire.
Usage: python run_benchmark.py [--category CATEGORY] [--difficulty DIFFICULTY] [--verbose]
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluator import BenchmarkRunner, BenchmarkResult
from claire_agent import ClaireAgent


def run_claire_benchmark(
    category: str = None,
    difficulty: str = None,
    verbose: bool = False,
    save_results: bool = True
) -> BenchmarkResult:
    """
    Run benchmark on Claire agent.

    Args:
        category: Filter by problem category (derivative, integral, limit, equation)
        difficulty: Filter by difficulty (easy, medium, hard)
        verbose: Print detailed output
        save_results: Save results to JSON file

    Returns:
        BenchmarkResult with aggregated metrics
    """
    # Initialize
    dataset_path = Path(__file__).parent / "datasets" / "calculus_benchmark.json"
    runner = BenchmarkRunner(str(dataset_path))

    print("\n" + "=" * 60)
    print("Claire Benchmark Evaluation")
    print("=" * 60)

    # Initialize Claire agent in benchmark mode (direct answers)
    print("\nInitializing Claire agent in BENCHMARK mode...")
    agent = ClaireAgent(benchmark_mode=True)

    if not agent.executor:
        print("ERROR: Claire agent not initialized (missing API key?)")
        sys.exit(1)

    # Get problems
    problems = runner.get_problems(category=category, difficulty=difficulty)
    print(f"\nRunning {len(problems)} problems...")
    if category:
        print(f"  Category: {category}")
    if difficulty:
        print(f"  Difficulty: {difficulty}")

    # Run evaluation
    results = []
    for i, problem in enumerate(problems, 1):
        print(f"\n[{i}/{len(problems)}] {problem['id']}: {problem['problem'][:50]}...")

        # Query Claire
        start_time = time.time()
        try:
            response = agent.process_query(problem['problem'])
            output = response.get('output', '')
        except Exception as e:
            output = f"Error: {str(e)}"

        latency_ms = (time.time() - start_time) * 1000

        # Evaluate response
        result = runner.evaluate_response(
            problem=problem,
            response=output,
            latency_ms=latency_ms
        )
        results.append(result)

        # Print result
        status = "PASS" if result.is_correct else "FAIL"
        print(f"  Status: {status}")
        print(f"  Expected: {problem['answer']}")
        print(f"  Extracted: {result.extracted_answer or 'N/A'}")
        if verbose:
            print(f"  Response: {output[:200]}...")
        print(f"  Latency: {latency_ms:.0f}ms")

    # Aggregate results
    benchmark_result = runner.aggregate_results("Claire", results)

    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"\nOverall Accuracy: {benchmark_result.accuracy:.1%}")
    print(f"Correct: {benchmark_result.correct}/{benchmark_result.total_problems}")
    print(f"Errors: {benchmark_result.errors}")
    print(f"Average Latency: {benchmark_result.avg_latency_ms:.0f}ms")

    print("\nBy Category:")
    for cat, stats in benchmark_result.by_category.items():
        print(f"  {cat}: {stats['accuracy']:.1%} ({stats['correct']}/{stats['total']})")

    print("\nBy Difficulty:")
    for diff, stats in benchmark_result.by_difficulty.items():
        print(f"  {diff}: {stats['accuracy']:.1%} ({stats['correct']}/{stats['total']})")

    # Save results
    if save_results:
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"claire_benchmark_{timestamp}.json"

        # Convert to serializable format
        results_data = {
            'model_name': benchmark_result.model_name,
            'timestamp': benchmark_result.timestamp,
            'total_problems': benchmark_result.total_problems,
            'correct': benchmark_result.correct,
            'accuracy': benchmark_result.accuracy,
            'by_category': benchmark_result.by_category,
            'by_difficulty': benchmark_result.by_difficulty,
            'avg_latency_ms': benchmark_result.avg_latency_ms,
            'problems': [
                {
                    'id': r.problem_id,
                    'category': r.category,
                    'difficulty': r.difficulty,
                    'problem': r.problem,
                    'expected': r.expected_answer,
                    'extracted': r.extracted_answer,
                    'is_correct': r.is_correct,
                    'error': r.error,
                    'latency_ms': r.latency_ms
                }
                for r in results
            ]
        }

        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"\nResults saved to: {results_file}")

    return benchmark_result


def main():
    parser = argparse.ArgumentParser(description="Run Claire benchmark evaluation")
    parser.add_argument(
        '--category',
        choices=['derivative', 'integral', 'limit', 'equation'],
        help='Filter by problem category'
    )
    parser.add_argument(
        '--difficulty',
        choices=['easy', 'medium', 'hard'],
        help='Filter by difficulty level'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed output'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save results to file'
    )

    args = parser.parse_args()

    run_claire_benchmark(
        category=args.category,
        difficulty=args.difficulty,
        verbose=args.verbose,
        save_results=not args.no_save
    )


if __name__ == "__main__":
    main()
