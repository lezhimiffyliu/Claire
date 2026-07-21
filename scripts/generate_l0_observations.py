#!/usr/bin/env python3
"""
Generate L0 observations for problem parts.

Reads problems from /problems/*.json, generates one L0 "start" observation
per part using DeepSeek, outputs to web/src/data/tutorAssets/l0Observations.generated.js.

This is a PENDING REVIEW file - do not auto-merge into the main asset file.

Usage:
    python scripts/generate_l0_observations.py
    python scripts/generate_l0_observations.py --course 126
    python scripts/generate_l0_observations.py --dry-run
    python scripts/generate_l0_observations.py --resume  # continue from checkpoint
"""

import os
import json
import argparse
from collections import Counter
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# DeepSeek config
MODEL = "deepseek-chat"
BASE_URL = "https://api.deepseek.com"
MAX_TOKENS = 80

# Diversity control
DEMONSTRATIVES = {"that", "those", "this", "these"}
INTERJECTIONS = {"oh", "ah", "huh", "ooh", "hm", "hmm", "wait", "okay", "ok"}
MAX_RETRIES = 4
PREFIX_CAP = {"demonstrative": 2, "interjection": 2}  # Special caps; default is 2


def get_openai_client():
    """Get OpenAI-compatible client for DeepSeek."""
    from openai import OpenAI
    return OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=BASE_URL,
    )


def build_part_text(problem: dict, part: dict) -> str:
    """Build the full text for a problem part."""
    parts = []
    if problem.get("stem"):
        parts.append(problem["stem"])

    label = part.get("label")
    question = part.get("question_text", "")
    if label:
        parts.append(f"({label}) {question}")
    else:
        parts.append(question)

    return "\n\n".join(parts)


def build_prompt(part_text: str) -> str:
    """Build the prompt for generating an L0 observation."""
    return f"""You're a teacher standing next to a student, glancing at this
problem, and you mutter one quick remark.

Write ONE short, spoken-style remark — the kind of thing a teacher actually
says out loud while pointing at the page, not a written observation.

Style:
- Sound like real speech, not a maxim or a summary
- Point at something VISIBLE in the problem (a function, a structure, a bound),
  not a result you computed
- Casual phrasing is good: "watch the...", "that ... will cancel",
  "this one's...", "don't let the ... fool you", "the ... inside is the thing"
- Don't pad to hit a length. Short is fine. Usually 5–12 words feels right.
- No forced opening phrase. Start however a real person would.

Examples of the right voice (notice the variety in how they start):
- "Huh, that y² inside the arctan just cancels."
- "Oh — the radius is 0.8, not 1."
- "That denominator's actually a perfect square."
- "The exponent's got an x in it, not a constant."
- "First term grows way faster than the second."
- "That minus sign comes back to bite you later."
- "There's another layer tucked inside the cos."
- "The log's got something squared in there too."
- "Honestly this one's gentle once you see inside."
- "And the 3x⁴ is hiding inside the ln."
- "Top and bottom share a factor, by the way."
- "It's the shaded part that matters, not the rest."
- "Keep an eye on the two speeds' ratio."
- "Easy to flip that sign halfway through."
- "Those limits aren't bad to pin down, actually."

What NOT to do:
- Don't derive or compute anything
- Don't give steps or methods ("apply the chain rule twice")
- Don't give generic advice ("remember to check your work")
- Don't sound like AI ("the bounds are the real story")
- Don't start with "That" — vary your openings

Problem:
{part_text}

Your remark:"""


def first_word(text: str) -> str:
    """Extract first word, normalized."""
    return text.strip().strip('"\'').split()[0].lower().rstrip(",.—-:")


def prefix_key(text: str) -> str:
    """Get diversity key for prefix tracking. Groups similar starts together."""
    fw = first_word(text)
    if fw in DEMONSTRATIVES:
        return "demonstrative"
    if fw in INTERJECTIONS:
        return "interjection"
    return fw


def clean_observation(text: str) -> str:
    """Clean up observation text."""
    import re
    text = text.strip()
    # Remove markdown bold/italic
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
    # Remove quotes if present
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1]
    # Remove leading/trailing quotes again after markdown strip
    text = text.strip().strip('"\'').strip()
    return text


def call_model(client, part_text: str, temperature: float) -> Optional[str]:
    """Call the model once."""
    prompt = build_prompt(part_text)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return clean_observation(response.choices[0].message.content)
    except Exception as e:
        print(f"    API error: {e}")
        return None


def generate_observation_with_diversity(
    client,
    problem: dict,
    part: dict,
    seen_prefixes: Counter
) -> Optional[str]:
    """Generate observation with retry logic for diversity."""
    part_text = build_part_text(problem, part)

    obs = None
    for attempt in range(MAX_RETRIES):
        # Temperature increases with retries to force variety
        temp = 0.9 + attempt * 0.25
        obs = call_model(client, part_text, temp)

        if not obs:
            continue

        fw = first_word(obs)
        key = prefix_key(obs)
        cap = PREFIX_CAP.get(key, 2)  # Default cap is 2 for any prefix

        if seen_prefixes[key] < cap:
            seen_prefixes[key] += 1
            return obs

        # Retry with higher temperature
        if attempt < MAX_RETRIES - 1:
            print(f"    Retry {attempt + 1}: '{fw}' ({key}) overused, regenerating...")

    # Fallback: accept last attempt anyway
    if obs:
        key = prefix_key(obs)
        seen_prefixes[key] += 1
    return obs


def load_problems(problems_dir: Path, course: Optional[str] = None) -> list:
    """Load all problems from JSON files."""
    all_problems = []

    pattern = f"math{course}_*.json" if course else "math*.json"

    for json_file in sorted(problems_dir.glob(pattern)):
        try:
            with open(json_file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    for p in data:
                        p["_source_file"] = json_file.name
                    all_problems.extend(data)
        except Exception as e:
            print(f"Warning: Failed to load {json_file}: {e}")

    return all_problems


def load_checkpoint(checkpoint_path: Path) -> dict:
    """Load checkpoint if exists."""
    if checkpoint_path.exists():
        with open(checkpoint_path) as f:
            return json.load(f)
    return {}


def save_checkpoint(checkpoint_path: Path, observations: dict):
    """Save checkpoint."""
    with open(checkpoint_path, "w") as f:
        json.dump(observations, f, indent=2)


def generate_all_observations(problems: list, checkpoint_path: Path, resume: bool = False) -> dict:
    """Generate observations for all problem parts with diversity control."""
    observations = load_checkpoint(checkpoint_path) if resume else {}
    client = get_openai_client()
    seen_prefixes = Counter()  # Track across entire batch

    total_parts = sum(len(p.get("parts", [])) for p in problems)
    already_done = len(observations)
    print(f"Generating observations for {total_parts} parts ({already_done} already done)...")

    count = 0
    for problem in problems:
        problem_id = problem.get("id")
        if not problem_id:
            continue

        parts = problem.get("parts", [])
        for part in parts:
            label = part.get("label")
            key = f"{problem_id}_{label}" if label else problem_id

            # Skip if already in checkpoint
            if key in observations:
                count += 1
                continue

            count += 1
            print(f"  [{count}/{total_parts}] {key}")

            obs = generate_observation_with_diversity(client, problem, part, seen_prefixes)

            if obs:
                observations[key] = {"start": [obs]}
                print(f"    → {obs[:60]}{'...' if len(obs) > 60 else ''}")

            # Save checkpoint every 20
            if count % 20 == 0:
                save_checkpoint(checkpoint_path, observations)
                print(f"  (checkpoint saved, prefixes: {dict(seen_prefixes.most_common(5))})")

    save_checkpoint(checkpoint_path, observations)
    print(f"\nGenerated {len(observations)} observations")
    print(f"Prefix distribution: {dict(seen_prefixes.most_common(10))}")
    return observations


def write_js_output(observations: dict, output_path: Path):
    """Write observations to a JavaScript file."""
    lines = [
        "/**",
        " * GENERATED FILE - DO NOT EDIT DIRECTLY",
        " * ",
        " * L0 Observations generated by scripts/generate_l0_observations.py",
        " * Review and merge approved entries into l0Observations.js",
        " * ",
        f" * Generated: {__import__('datetime').datetime.now().isoformat()}",
        f" * Count: {len(observations)} observations",
        " */",
        "",
        "export const L0_OBSERVATIONS_GENERATED = {",
    ]

    for key, value in sorted(observations.items()):
        start_text = value["start"][0]
        # Escape for JS string
        escaped = start_text.replace("\\", "\\\\").replace("'", "\\'")
        lines.append(f"  '{key}': {{")
        lines.append(f"    start: ['{escaped}'],")
        lines.append(f"  }},")

    lines.append("}")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Wrote {len(observations)} observations to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate L0 observations for problems")
    parser.add_argument("--course", type=str, help="Course number (124, 125, 126)")
    parser.add_argument("--dry-run", action="store_true", help="Don't call API, just test flow")
    parser.add_argument("--limit", type=int, help="Limit number of problems to process")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    args = parser.parse_args()

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    problems_dir = project_root / "problems"
    output_path = project_root / "web" / "src" / "data" / "tutorAssets" / "l0Observations.generated.js"
    checkpoint_path = project_root / "web" / "src" / "data" / "tutorAssets" / "l0_checkpoint.json"

    # Load problems
    problems = load_problems(problems_dir, args.course)
    print(f"Loaded {len(problems)} problems from {problems_dir}")

    if args.limit:
        problems = problems[:args.limit]
        print(f"Limited to {len(problems)} problems")

    # Generate observations
    if args.dry_run:
        # Dry run - just count
        total_parts = sum(len(p.get("parts", [])) for p in problems)
        print(f"[DRY RUN] Would generate {total_parts} observations")
        observations = {f"dry_run_{i}": {"start": ["[DRY RUN]"]} for i in range(min(5, total_parts))}
    else:
        observations = generate_all_observations(problems, checkpoint_path, args.resume)

    # Write output
    write_js_output(observations, output_path)

    print("\nNext steps:")
    print(f"1. Review: {output_path}")
    print("2. Approve good entries, edit or remove bad ones")
    print("3. Merge approved entries into l0Observations.js")


if __name__ == "__main__":
    main()
