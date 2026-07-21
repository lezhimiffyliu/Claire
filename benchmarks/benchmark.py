#!/usr/bin/env python3
"""
Claire Benchmark System v2.0
Standard evaluation framework for comparing LLM math capabilities.

Features:
- Standardized API calls (latest OpenAI/Anthropic SDKs)
- Unified inference parameters
- Complete logging and transparency
- Strict answer matching

Usage:
    python benchmark.py --models claire,gpt-4o,claude-sonnet --limit 50
"""

import os
import sys
import json
import time
import re
import random
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Import SymPy-based evaluator
from evaluator import evaluate as sympy_evaluate


# =============================================================================
# CONFIGURATION
# =============================================================================

# Fixed random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Unified inference parameters
INFERENCE_CONFIG = {
    'temperature': 0,
    'max_tokens': 4096,
    'stream': False,
}

# Standard system prompt for all models
SYSTEM_PROMPT = """You are a precise mathematical problem solver.
Solve the given problem step by step.
Put your final answer inside \\boxed{} at the end of your solution.
Do not include units or explanations inside the box, only the final numerical or symbolic answer."""

# User prompt template
USER_PROMPT_TEMPLATE = """Problem: {problem}

Solve this problem step by step. Put your final answer in \\boxed{{}}."""

# Model configurations
# Updated to use latest available models
MODEL_CONFIGS = {
    'gpt-4-turbo': {
        'provider': 'openai',
        'model_id': 'gpt-4-turbo',
        'display_name': 'GPT-4 Turbo',
    },
    'gpt-4': {
        'provider': 'openai',
        'model_id': 'gpt-4',
        'display_name': 'GPT-4',
    },
    'gpt-3.5-turbo': {
        'provider': 'openai',
        'model_id': 'gpt-3.5-turbo',
        'display_name': 'GPT-3.5 Turbo',
    },
    'claude-sonnet': {
        'provider': 'anthropic',
        'model_id': 'claude-sonnet-4-20250514',
        'display_name': 'Claude Sonnet 4',
    },
    'claude-haiku': {
        'provider': 'anthropic',
        'model_id': 'claude-3-5-haiku-20241022',
        'display_name': 'Claude 3.5 Haiku',
    },
    'claire': {
        'provider': 'claire',
        'model_id': 'claire-v1',
        'display_name': 'Claire (Claude+SymPy)',
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ProblemResult:
    """Result for a single problem evaluation."""
    problem_id: str
    problem_text: str
    ground_truth: str
    model_name: str
    raw_response: str
    parsed_answer: Optional[str]
    is_correct: bool
    is_truncated: bool
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    error: Optional[str]


@dataclass
class BenchmarkSummary:
    """Summary statistics for a benchmark run."""
    model_name: str
    total_problems: int
    correct_count: int
    accuracy: float
    avg_input_tokens: float
    avg_output_tokens: float
    avg_total_tokens: float
    avg_latency_ms: float
    truncated_count: int
    error_count: int
    timestamp: str


# =============================================================================
# ANSWER EXTRACTION
# =============================================================================

def extract_boxed_answer(response: str) -> Optional[str]:
    """
    Extract answer from \\boxed{...} with proper nested brace handling.
    Returns None if no boxed answer found.
    """
    if not response:
        return None

    # Find \boxed{ with possible variations
    patterns = [r'\\boxed\s*\{', r'\\boxed\{', r'boxed\s*\{']

    for pattern in patterns:
        match = re.search(pattern, response)
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
                answer = response[start:end-1].strip()
                return answer

    return None


def check_answer(predicted: str, ground_truth: str) -> Tuple[bool, str, str]:
    """
    Check answer equivalence using SymPy evaluator.
    Returns (is_correct, method, details).
    """
    if not predicted or not ground_truth:
        return False, 'empty', 'empty input'

    result = sympy_evaluate(predicted, ground_truth)
    return result.is_equivalent, result.method, result.details


# =============================================================================
# MODEL INTERFACES
# =============================================================================

class OpenAIModel:
    """OpenAI API interface using latest SDK."""

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.client = None

    def _init_client(self):
        if self.client is None:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = OpenAI(api_key=api_key)

    def query(self, problem: str) -> Dict[str, Any]:
        """Single query, no streaming, no tools."""
        self._init_client()

        user_prompt = USER_PROMPT_TEMPLATE.format(problem=problem)

        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=INFERENCE_CONFIG['temperature'],
                max_tokens=INFERENCE_CONFIG['max_tokens'],
                stream=INFERENCE_CONFIG['stream'],
            )

            latency_ms = (time.time() - start_time) * 1000

            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            return {
                'response': content,
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'is_truncated': finish_reason == 'length',
                'latency_ms': latency_ms,
                'error': None,
            }

        except Exception as e:
            return {
                'response': '',
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'is_truncated': False,
                'latency_ms': (time.time() - start_time) * 1000,
                'error': str(e),
            }


class AnthropicModel:
    """Anthropic API interface using latest SDK (v1/messages)."""

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.client = None

    def _init_client(self):
        if self.client is None:
            import anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = anthropic.Anthropic(api_key=api_key)

    def query(self, problem: str) -> Dict[str, Any]:
        """Single query, no streaming, no tools."""
        self._init_client()

        user_prompt = USER_PROMPT_TEMPLATE.format(problem=problem)

        start_time = time.time()

        try:
            response = self.client.messages.create(
                model=self.model_id,
                max_tokens=INFERENCE_CONFIG['max_tokens'],
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=INFERENCE_CONFIG['temperature'],
            )

            latency_ms = (time.time() - start_time) * 1000

            content = response.content[0].text

            return {
                'response': content,
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
                'is_truncated': response.stop_reason == 'max_tokens',
                'latency_ms': latency_ms,
                'error': None,
            }

        except Exception as e:
            return {
                'response': '',
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'is_truncated': False,
                'latency_ms': (time.time() - start_time) * 1000,
                'error': str(e),
            }


class ClaireModel:
    """Claire agent interface (Claude + SymPy tools)."""

    def __init__(self):
        self.agent = None

    def _init_agent(self):
        if self.agent is None:
            from claire_agent_old import ClaireAgent
            self.agent = ClaireAgent(benchmark_mode=True)

    def query(self, problem: str) -> Dict[str, Any]:
        """Single query using Claire's tool-augmented approach."""
        self._init_agent()

        start_time = time.time()

        try:
            result = self.agent.process_query(problem)
            latency_ms = (time.time() - start_time) * 1000

            content = result.get('output', '')

            return {
                'response': content,
                'input_tokens': 0,  # Not tracked for Claire
                'output_tokens': 0,
                'total_tokens': 0,
                'is_truncated': False,
                'latency_ms': latency_ms,
                'error': None,
            }

        except Exception as e:
            return {
                'response': '',
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'is_truncated': False,
                'latency_ms': (time.time() - start_time) * 1000,
                'error': str(e),
            }


def get_model(model_name: str):
    """Factory function to get model interface."""
    if model_name not in MODEL_CONFIGS:
        raise ValueError(f"Unknown model: {model_name}")

    config = MODEL_CONFIGS[model_name]
    provider = config['provider']

    if provider == 'openai':
        return OpenAIModel(config['model_id'])
    elif provider == 'anthropic':
        return AnthropicModel(config['model_id'])
    elif provider == 'claire':
        return ClaireModel()
    else:
        raise ValueError(f"Unknown provider: {provider}")


# =============================================================================
# BENCHMARK RUNNER
# =============================================================================

def load_dataset(path: str, limit: Optional[int] = None) -> List[Dict]:
    """Load benchmark dataset."""
    with open(path, 'r') as f:
        data = json.load(f)

    problems = data.get('problems', [])

    if limit:
        problems = problems[:limit]

    return problems


def run_benchmark(
    model_names: List[str],
    dataset_path: str,
    limit: Optional[int] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, BenchmarkSummary]:
    """
    Run benchmark evaluation.

    Returns dict of model_name -> BenchmarkSummary
    """
    # Load dataset
    problems = load_dataset(dataset_path, limit)

    print("=" * 80)
    print("CLAIRE BENCHMARK SYSTEM v2.0")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Random Seed: {RANDOM_SEED}")
    print(f"Dataset: {dataset_path}")
    print(f"Total Problems: {len(problems)}")
    print(f"Models: {', '.join(model_names)}")
    print(f"Inference Config: {INFERENCE_CONFIG}")
    print("=" * 80)

    # Initialize models
    models = {}
    for name in model_names:
        try:
            models[name] = get_model(name)
            print(f"[OK] Initialized: {MODEL_CONFIGS[name]['display_name']}")
        except Exception as e:
            print(f"[FAIL] {name}: {e}")

    if not models:
        print("ERROR: No models available")
        return {}

    print("=" * 80)

    # Run evaluation
    all_results: Dict[str, List[ProblemResult]] = {name: [] for name in models}

    for i, problem in enumerate(problems, 1):
        problem_id = problem.get('id', str(i))
        problem_text = problem.get('problem', '')
        ground_truth = problem.get('answer', '')

        print(f"\n{'='*80}")
        print(f"PROBLEM {i}/{len(problems)}: {problem_id}")
        print(f"{'='*80}")
        print(f"Problem: {problem_text[:200]}{'...' if len(problem_text) > 200 else ''}")
        print(f"Ground Truth: {ground_truth}")
        print("-" * 80)

        for model_name, model in models.items():
            display_name = MODEL_CONFIGS[model_name]['display_name']

            # Query model
            result = model.query(problem_text)

            # Extract answer
            parsed_answer = extract_boxed_answer(result['response'])

            # For Claire, also try "Answer: X" pattern
            if model_name == 'claire' and not parsed_answer:
                match = re.search(r'[Aa]nswer:\s*(.+?)(?:\n|$)', result['response'])
                if match:
                    parsed_answer = match.group(1).strip()

            # Check correctness using SymPy evaluator
            is_correct, eval_method, eval_details = check_answer(parsed_answer, ground_truth)

            # Create result
            problem_result = ProblemResult(
                problem_id=problem_id,
                problem_text=problem_text,
                ground_truth=ground_truth,
                model_name=model_name,
                raw_response=result['response'],
                parsed_answer=parsed_answer,
                is_correct=is_correct,
                is_truncated=result['is_truncated'],
                input_tokens=result['input_tokens'],
                output_tokens=result['output_tokens'],
                total_tokens=result['total_tokens'],
                latency_ms=result['latency_ms'],
                error=result['error'],
            )

            all_results[model_name].append(problem_result)

            # Print result
            status = "✓ CORRECT" if is_correct else "✗ WRONG"
            if result['error']:
                status = f"✗ ERROR: {result['error']}"

            print(f"\n[{display_name}]")
            print(f"  Status: {status}")
            print(f"  Parsed Answer: {parsed_answer or 'N/A'}")
            print(f"  Eval Method: {eval_method}")
            print(f"  Tokens: {result['total_tokens']} (in:{result['input_tokens']}, out:{result['output_tokens']})")
            print(f"  Latency: {result['latency_ms']:.0f}ms")
            print(f"  Truncated: {result['is_truncated']}")
            print(f"  Raw Response (first 300 chars):")
            print(f"    {result['response'][:300]}{'...' if len(result['response']) > 300 else ''}")

    # Compute summaries
    summaries = {}

    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    for model_name, results in all_results.items():
        display_name = MODEL_CONFIGS[model_name]['display_name']

        total = len(results)
        correct = sum(1 for r in results if r.is_correct)
        accuracy = correct / total if total > 0 else 0

        avg_input = sum(r.input_tokens for r in results) / total if total > 0 else 0
        avg_output = sum(r.output_tokens for r in results) / total if total > 0 else 0
        avg_total = sum(r.total_tokens for r in results) / total if total > 0 else 0
        avg_latency = sum(r.latency_ms for r in results) / total if total > 0 else 0

        truncated = sum(1 for r in results if r.is_truncated)
        errors = sum(1 for r in results if r.error)

        summary = BenchmarkSummary(
            model_name=display_name,
            total_problems=total,
            correct_count=correct,
            accuracy=accuracy,
            avg_input_tokens=avg_input,
            avg_output_tokens=avg_output,
            avg_total_tokens=avg_total,
            avg_latency_ms=avg_latency,
            truncated_count=truncated,
            error_count=errors,
            timestamp=datetime.now().isoformat(),
        )

        summaries[model_name] = summary

        print(f"\n{display_name}")
        print("-" * 40)
        print(f"  Total Problems:    {total}")
        print(f"  Correct:           {correct}")
        print(f"  Accuracy:          {accuracy:.1%}")
        print(f"  Avg Input Tokens:  {avg_input:.0f}")
        print(f"  Avg Output Tokens: {avg_output:.0f}")
        print(f"  Avg Total Tokens:  {avg_total:.0f}")
        print(f"  Avg Latency:       {avg_latency:.0f}ms")
        print(f"  Truncated:         {truncated}")
        print(f"  Errors:            {errors}")

    # Save results
    if output_dir is None:
        output_dir = Path(__file__).parent / "results"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"benchmark_{timestamp}.json"

    output_data = {
        'metadata': {
            'timestamp': timestamp,
            'random_seed': RANDOM_SEED,
            'inference_config': INFERENCE_CONFIG,
            'system_prompt': SYSTEM_PROMPT,
            'user_prompt_template': USER_PROMPT_TEMPLATE,
            'dataset': str(dataset_path),
            'num_problems': len(problems),
            'models': model_names,
        },
        'summaries': {name: asdict(s) for name, s in summaries.items()},
        'results': {
            name: [asdict(r) for r in results]
            for name, results in all_results.items()
        },
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")

    return summaries


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Claire Benchmark System v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python benchmark.py --models claire,gpt-4o --limit 20
    python benchmark.py --models claude-sonnet --dataset custom.json
    python benchmark.py --models claire,gpt-4o,claude-sonnet --limit 50
        """
    )

    parser.add_argument(
        '--models',
        default='claire',
        help=f"Comma-separated models: {', '.join(MODEL_CONFIGS.keys())}"
    )

    parser.add_argument(
        '--dataset',
        default=str(Path(__file__).parent / "datasets" / "math_calculus.json"),
        help="Path to dataset JSON file"
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help="Limit number of problems"
    )

    parser.add_argument(
        '--output-dir',
        default=None,
        help="Output directory for results"
    )

    args = parser.parse_args()

    model_names = [m.strip() for m in args.models.split(',')]

    run_benchmark(
        model_names=model_names,
        dataset_path=args.dataset,
        limit=args.limit,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
