#!/usr/bin/env python3
"""
Compare Claire vs GPT vs Claude on MATH benchmark.
Uses standardized prompts and answer extraction for fair comparison.

Usage: python compare_models.py [--models claire,gpt-4,claude] [--limit 50]
"""

import os
import sys
import json
import time
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from evaluator import MathEvaluator, BenchmarkRunner


# Standard prompt template - all models use this
MATH_EVAL_PROMPT = """Solve this math problem step by step. Put your final answer in \\boxed{{}}.

Problem: {problem}

Solution:"""


@dataclass
class ModelConfig:
    """Configuration for a model."""
    name: str
    provider: str  # 'claire', 'openai', 'anthropic'
    model_id: str = None
    api_key_env: str = None
    use_tools: bool = False


# Available models
MODELS = {
    'claire': ModelConfig(
        name='Claire (Claude+SymPy)',
        provider='claire',
        use_tools=True
    ),
    'claude': ModelConfig(
        name='Claude Sonnet',
        provider='anthropic',
        model_id='claude-sonnet-4-20250514',
        api_key_env='ANTHROPIC_API_KEY',
        use_tools=False
    ),
    'gpt-4': ModelConfig(
        name='GPT-4 Turbo',
        provider='openai',
        model_id='gpt-4-turbo-preview',
        api_key_env='OPENAI_API_KEY',
        use_tools=False
    ),
    'gpt-3.5': ModelConfig(
        name='GPT-3.5 Turbo',
        provider='openai',
        model_id='gpt-3.5-turbo',
        api_key_env='OPENAI_API_KEY',
        use_tools=False
    ),
}


def extract_boxed_answer(response: str) -> Optional[str]:
    """Extract answer from \\boxed{...} with proper nested brace handling."""
    if not response:
        return None

    # Pattern 1: \boxed{...} with nested braces
    match = re.search(r'\\boxed\s*\{', response)
    if match:
        start = match.end()
        depth = 1
        end = start
        while end < len(response) and depth > 0:
            if response[end] == '{':
                depth += 1
            elif response[end] == '}':
                depth -= 1
            end += 1
        if depth == 0:
            return response[start:end-1].strip()

    # Pattern 2: boxed{...} (without backslash)
    match = re.search(r'boxed\s*\{', response)
    if match:
        start = match.end()
        depth = 1
        end = start
        while end < len(response) and depth > 0:
            if response[end] == '{':
                depth += 1
            elif response[end] == '}':
                depth -= 1
            end += 1
        if depth == 0:
            return response[start:end-1].strip()

    # Pattern 3: **Answer:** or Answer:
    match = re.search(r'\*?\*?[Aa]nswer:?\*?\*?\s*(.+?)(?:\n|$)', response)
    if match:
        answer = match.group(1).strip()
        # Clean up markdown
        answer = re.sub(r'\*\*(.+?)\*\*', r'\1', answer)
        # Clean up LaTeX delimiters
        answer = answer.strip('$').strip()
        return answer

    # Pattern 4: "The answer is X" or "= X"
    match = re.search(r'(?:answer is|equals?|=)\s*[:\s]*\$?([^\n\.,\$]+)\$?', response, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 5: Last boxed-like expression
    # Look for patterns like $X$ at end of response
    match = re.search(r'\$([^$]+)\$\s*$', response)
    if match:
        return match.group(1).strip()

    return None


class ModelInterface:
    """Interface for querying different models with standardized prompts."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self._client = None

    def query(self, problem: str) -> Dict[str, Any]:
        """
        Query the model with a standardized prompt.

        Returns:
        {
            'response': str,      # Full response
            'answer': str,        # Extracted answer
            'latency_ms': float,
            'tokens': int,
            'error': str or None
        }
        """
        try:
            if self.config.provider == 'claire':
                return self._query_claire(problem)
            elif self.config.provider == 'openai':
                return self._query_openai(problem)
            elif self.config.provider == 'anthropic':
                return self._query_anthropic(problem)
            else:
                raise ValueError(f"Unknown provider: {self.config.provider}")
        except Exception as e:
            return {
                'response': '',
                'answer': None,
                'latency_ms': 0,
                'tokens': 0,
                'error': str(e)
            }

    def _query_claire(self, problem: str) -> Dict[str, Any]:
        """Query Claire agent (uses tools)."""
        from claire_agent_old import ClaireAgent

        if self._client is None:
            self._client = ClaireAgent(benchmark_mode=True)

        start = time.time()
        result = self._client.process_query(problem)
        latency = (time.time() - start) * 1000

        response = result.get('output', '')
        answer = extract_boxed_answer(response)

        # Claire's benchmark mode outputs "Answer: X"
        if not answer:
            match = re.search(r'[Aa]nswer:\s*(.+?)(?:\n|$)', response)
            if match:
                answer = match.group(1).strip()

        return {
            'response': response,
            'answer': answer,
            'latency_ms': latency,
            'tokens': 0,
            'error': None
        }

    def _query_openai(self, problem: str) -> Dict[str, Any]:
        """Query OpenAI model with standardized prompt."""
        api_key = os.getenv(self.config.api_key_env)
        if not api_key:
            raise ValueError(f"Missing API key: {self.config.api_key_env}")

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")

        if self._client is None:
            self._client = OpenAI(api_key=api_key)

        prompt = MATH_EVAL_PROMPT.format(problem=problem)

        start = time.time()
        response = self._client.chat.completions.create(
            model=self.config.model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1024
        )
        latency = (time.time() - start) * 1000

        output = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        answer = extract_boxed_answer(output)

        return {
            'response': output,
            'answer': answer,
            'latency_ms': latency,
            'tokens': tokens,
            'error': None
        }

    def _query_anthropic(self, problem: str) -> Dict[str, Any]:
        """Query Anthropic model with standardized prompt."""
        api_key = os.getenv(self.config.api_key_env)
        if not api_key:
            raise ValueError(f"Missing API key: {self.config.api_key_env}")

        try:
            import anthropic
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")

        if self._client is None:
            self._client = anthropic.Anthropic(api_key=api_key)

        prompt = MATH_EVAL_PROMPT.format(problem=problem)

        start = time.time()
        response = self._client.messages.create(
            model=self.config.model_id,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        latency = (time.time() - start) * 1000

        output = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        answer = extract_boxed_answer(output)

        return {
            'response': output,
            'answer': answer,
            'latency_ms': latency,
            'tokens': tokens,
            'error': None
        }


def compare_models(
    model_names: List[str],
    dataset_path: str = None,
    limit: int = None,
    category: str = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run comparison across multiple models on MATH dataset.
    """
    # Load dataset
    if dataset_path is None:
        dataset_path = Path(__file__).parent / "datasets" / "math_calculus.json"

    with open(dataset_path) as f:
        data = json.load(f)

    problems = data['problems']

    # Filter by category if specified
    if category:
        problems = [p for p in problems if p.get('category') == category]

    # Limit number of problems
    if limit:
        problems = problems[:limit]

    print("\n" + "=" * 70)
    print("MATH Benchmark - Model Comparison")
    print("=" * 70)

    # Initialize models
    models = {}
    for name in model_names:
        if name not in MODELS:
            print(f"WARNING: Unknown model '{name}', skipping")
            continue
        config = MODELS[name]
        try:
            # Test API key
            if config.api_key_env and not os.getenv(config.api_key_env):
                print(f"WARNING: {config.api_key_env} not set, skipping {name}")
                continue
            models[name] = ModelInterface(config)
            print(f"Initialized: {config.name}")
        except Exception as e:
            print(f"Failed to initialize {name}: {e}")

    if not models:
        print("ERROR: No models available")
        sys.exit(1)

    print(f"\nRunning {len(problems)} problems on {len(models)} models...")
    print(f"Using standardized prompt with \\boxed{{}} format\n")

    # Initialize evaluator
    evaluator = MathEvaluator()

    # Results storage
    results = {name: [] for name in models}
    total_correct = {name: 0 for name in models}
    total_latency = {name: 0 for name in models}
    total_tokens = {name: 0 for name in models}

    # Run evaluation
    for i, problem in enumerate(problems, 1):
        problem_text = problem['problem']
        expected = problem.get('answer', '')

        print(f"[{i}/{len(problems)}] {problem.get('id', i)}")
        if verbose:
            print(f"  Problem: {problem_text[:60]}...")
            print(f"  Expected: {expected}")

        for model_name, interface in models.items():
            result = interface.query(problem_text)

            # Check correctness
            is_correct = False
            if result['answer'] and expected:
                is_correct, _ = evaluator.check_equivalence(expected, result['answer'])

            results[model_name].append({
                'problem_id': problem.get('id', str(i)),
                'problem': problem_text,
                'expected': expected,
                'predicted': result['answer'],
                'is_correct': is_correct,
                'latency_ms': result['latency_ms'],
                'tokens': result['tokens'],
                'error': result['error'],
                'full_response': result['response'][:500] if verbose else None
            })

            if is_correct:
                total_correct[model_name] += 1
            total_latency[model_name] += result['latency_ms']
            total_tokens[model_name] += result['tokens']

            status = "✓" if is_correct else "✗"
            print(f"  {MODELS[model_name].name}: {status} ({result['latency_ms']:.0f}ms) "
                  f"→ {result['answer'] or 'N/A'}")

    # Print summary
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)

    print(f"\n{'Model':<30} {'Accuracy':>10} {'Avg Latency':>12} {'Tokens':>10}")
    print("-" * 65)

    for name in sorted(models.keys(), key=lambda x: total_correct[x], reverse=True):
        config = MODELS[name]
        n = len(problems)
        acc = total_correct[name] / n if n > 0 else 0
        avg_lat = total_latency[name] / n if n > 0 else 0
        print(f"{config.name:<30} {acc:>9.1%} {avg_lat:>10.0f}ms {total_tokens[name]:>10}")

    # Save results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = results_dir / f"comparison_{timestamp}.json"

    output_data = {
        'timestamp': timestamp,
        'dataset': str(dataset_path),
        'num_problems': len(problems),
        'models': model_names,
        'summary': {
            name: {
                'accuracy': total_correct[name] / len(problems) if problems else 0,
                'correct': total_correct[name],
                'total': len(problems),
                'avg_latency_ms': total_latency[name] / len(problems) if problems else 0,
                'total_tokens': total_tokens[name]
            }
            for name in models
        },
        'results': results
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return output_data


def main():
    parser = argparse.ArgumentParser(description="Compare models on MATH benchmark")
    parser.add_argument(
        '--models',
        default='claire,gpt-4',
        help='Comma-separated list of models (claire, gpt-4, gpt-3.5, claude)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Limit number of problems (default: 20)'
    )
    parser.add_argument(
        '--category',
        choices=['derivative', 'integral', 'limit', 'equation', 'other'],
        help='Filter by problem category'
    )
    parser.add_argument(
        '--dataset',
        help='Path to dataset JSON file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed output'
    )

    args = parser.parse_args()

    model_names = [m.strip() for m in args.models.split(',')]

    compare_models(
        model_names=model_names,
        dataset_path=args.dataset,
        limit=args.limit,
        category=args.category,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
