#!/usr/bin/env python3
"""
Download and process MATH dataset for Claire benchmark.
Filters for calculus-related problems.

MATH dataset: https://github.com/hendrycks/math
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict


def download_math_dataset():
    """Download MATH dataset from HuggingFace."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("Installing datasets library...")
        os.system("pip install datasets")
        from datasets import load_dataset

    print("Downloading MATH dataset from HuggingFace...")

    # Available subsets: algebra, counting_and_probability, geometry,
    # intermediate_algebra, number_theory, prealgebra, precalculus
    subsets = ['precalculus', 'intermediate_algebra', 'algebra']

    all_problems = []

    for subset in subsets:
        print(f"  Loading {subset}...")
        try:
            ds = load_dataset('EleutherAI/hendrycks_math', subset, split='test')
            for item in ds:
                all_problems.append({
                    'problem': item['problem'],
                    'solution': item['solution'],
                    'level': item['level'],
                    'type': item['type'],
                    'subset': subset
                })
        except Exception as e:
            print(f"    Failed: {e}")

    return all_problems


def extract_calculus_problems(problems: List[Dict]) -> List[Dict]:
    """Extract calculus-related problems from MATH dataset."""
    calculus_problems = []

    # Calculus-related keywords
    calculus_keywords = [
        'derivative', 'differentiate', 'd/dx', "f'(x)",
        'integral', 'integrate', 'antiderivative',
        'limit', 'lim', 'approaches',
        'continuous', 'continuity',
        'tangent line', 'slope',
        'rate of change',
        'taylor', 'maclaurin',
        'maximum', 'minimum', 'extrema',
        'asymptote',
        'logarithm', 'log', 'ln',
        'exponential', 'e^',
        'trigonometric', 'sin', 'cos', 'tan',
    ]

    for item in problems:
        problem_text = item['problem'].lower()

        # Check if calculus-related
        is_calculus = any(kw in problem_text for kw in calculus_keywords)

        if is_calculus:
            # Extract answer from solution
            answer = extract_answer_from_solution(item['solution'])

            calculus_problems.append({
                'id': f"math_{len(calculus_problems):04d}",
                'source': 'MATH',
                'category': categorize_problem(problem_text),
                'difficulty': map_level_to_difficulty(item['level']),
                'problem': item['problem'],
                'solution': item['solution'],
                'answer': answer,
                'original_type': item['type'],
                'subset': item['subset']
            })

    return calculus_problems


def extract_answer_from_solution(solution: str) -> str:
    """Extract the final answer from a MATH dataset solution."""
    # MATH dataset uses \boxed{answer} format
    # Need to handle nested braces like \boxed{\frac{1}{2}}

    # Find \boxed{ and then match balanced braces
    match = re.search(r'\\boxed\{', solution)
    if match:
        start = match.end()
        depth = 1
        end = start
        while end < len(solution) and depth > 0:
            if solution[end] == '{':
                depth += 1
            elif solution[end] == '}':
                depth -= 1
            end += 1
        if depth == 0:
            return solution[start:end-1]

    # Fallback: look for last "=" in solution
    equals_match = re.findall(r'=\s*([^\s\.\,]+)', solution)
    if equals_match:
        return equals_match[-1]

    return ""


def categorize_problem(problem_text: str) -> str:
    """Categorize problem into derivative/integral/limit/equation/other."""
    problem_lower = problem_text.lower()

    if any(kw in problem_lower for kw in ['derivative', 'differentiate', 'd/dx', 'tangent', "f'("]):
        return 'derivative'
    elif any(kw in problem_lower for kw in ['integral', 'integrate', 'antiderivative', 'area under']):
        return 'integral'
    elif any(kw in problem_lower for kw in ['limit', 'lim', 'approaches', 'tends to']):
        return 'limit'
    elif any(kw in problem_lower for kw in ['solve', 'find x', 'find the value', 'root']):
        return 'equation'
    else:
        return 'other'


def map_level_to_difficulty(level: str) -> str:
    """Map MATH dataset level to easy/medium/hard."""
    if 'Level 1' in level or 'Level 2' in level:
        return 'easy'
    elif 'Level 3' in level:
        return 'medium'
    else:
        return 'hard'


def save_dataset(problems: List[Dict], output_path: Path):
    """Save processed dataset to JSON."""
    # Count by category
    categories = {}
    difficulties = {}
    for p in problems:
        cat = p['category']
        diff = p['difficulty']
        categories[cat] = categories.get(cat, 0) + 1
        difficulties[diff] = difficulties.get(diff, 0) + 1

    dataset = {
        'metadata': {
            'name': 'MATH Dataset - Calculus Subset',
            'version': '1.0',
            'source': 'https://github.com/hendrycks/math',
            'description': 'Calculus-related problems extracted from MATH dataset',
            'total_problems': len(problems),
            'by_category': categories,
            'by_difficulty': difficulties
        },
        'problems': problems
    }

    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)

    print(f"\nSaved {len(problems)} problems to {output_path}")
    print(f"By category: {categories}")
    print(f"By difficulty: {difficulties}")


def main():
    output_dir = Path(__file__).parent / "datasets"
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("MATH Dataset Downloader for Claire Benchmark")
    print("=" * 60)

    # Download dataset
    print("\nDownloading MATH dataset...")
    all_problems = download_math_dataset()
    print(f"Downloaded {len(all_problems)} problems total")

    # Extract calculus-related
    print("\nExtracting calculus-related problems...")
    calculus_problems = extract_calculus_problems(all_problems)

    if calculus_problems:
        output_path = output_dir / "math_calculus.json"
        save_dataset(calculus_problems, output_path)
    else:
        print("No calculus problems found!")

    print("\nDone!")


if __name__ == "__main__":
    main()
