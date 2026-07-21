#!/usr/bin/env python3
"""
Claude Code Usage Report

Scans ~/.claude/projects/**/*.jsonl to calculate daily token usage.
Outputs to ~/.claude_usage/daily_usage.csv and daily_usage.json

Usage:
    python scripts/claude_usage_report.py           # Today only
    python scripts/claude_usage_report.py --date 2026-05-16
    python scripts/claude_usage_report.py --all     # All history
"""

import argparse
import csv
import json
import os
from datetime import datetime, date
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude" / "projects"
OUT_DIR = Path.home() / ".claude_usage"
CSV_PATH = OUT_DIR / "daily_usage.csv"
JSON_PATH = OUT_DIR / "daily_usage.json"

# Pricing per 1M tokens (USD) - Claude Opus 4.5 rates
# Adjust these based on your actual model/plan
PRICE_CONFIG = {
    "input": 15.0,           # $15/MTok for Opus input
    "output": 75.0,          # $75/MTok for Opus output
    "cache_read": 1.50,      # $1.50/MTok (10% of input)
    "cache_creation": 18.75, # $18.75/MTok (125% of input)
}


def file_date(path: Path) -> str:
    """Get file modification date as YYYY-MM-DD string."""
    return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()


def project_name(path: Path) -> str:
    """Extract project name from path."""
    try:
        return path.relative_to(CLAUDE_DIR).parts[0]
    except Exception:
        return "unknown"


def parse_usage(path: Path) -> dict:
    """Parse a session .jsonl file and sum up token usage."""
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
    }

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                d = json.loads(line)
                # Token usage is nested in message.usage
                u = d.get("message", {})
                if isinstance(u, dict):
                    u = u.get("usage", {})
                    if isinstance(u, dict):
                        totals["input_tokens"] += u.get("input_tokens", 0) or 0
                        totals["output_tokens"] += u.get("output_tokens", 0) or 0
                        totals["cache_read_tokens"] += u.get("cache_read_input_tokens", 0) or 0
                        totals["cache_creation_tokens"] += u.get("cache_creation_input_tokens", 0) or 0
            except json.JSONDecodeError:
                continue
            except Exception:
                continue

    return totals


def estimate_cost(t: dict) -> float:
    """Estimate API cost based on token counts and PRICE_CONFIG."""
    return (
        t["input_tokens"] / 1_000_000 * PRICE_CONFIG["input"]
        + t["output_tokens"] / 1_000_000 * PRICE_CONFIG["output"]
        + t["cache_read_tokens"] / 1_000_000 * PRICE_CONFIG["cache_read"]
        + t["cache_creation_tokens"] / 1_000_000 * PRICE_CONFIG["cache_creation"]
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate Claude Code token usage report"
    )
    parser.add_argument(
        "--date",
        help="Only report usage for this date (YYYY-MM-DD)",
        metavar="YYYY-MM-DD"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Report all historical usage (ignore date filter)"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show daily summary instead of per-session breakdown"
    )
    args = parser.parse_args()

    target_date = args.date or date.today().isoformat()
    rows = []

    if not CLAUDE_DIR.exists():
        print(f"Claude projects directory not found: {CLAUDE_DIR}")
        return

    for f in CLAUDE_DIR.glob("**/*.jsonl"):
        d = file_date(f)
        if not args.all and d != target_date:
            continue

        usage = parse_usage(f)
        total = sum(usage.values())
        if total == 0:
            continue

        row = {
            "date": d,
            "project": project_name(f),
            "session_file": f.name,
            **usage,
            "total_tokens": total,
            "estimated_api_cost_usd": round(estimate_cost(usage), 4),
        }
        rows.append(row)

    # Sort by date descending, then by project
    rows.sort(key=lambda r: (r["date"], r["project"]), reverse=True)

    # Create output directory
    OUT_DIR.mkdir(exist_ok=True)

    # Write CSV
    fields = [
        "date", "project", "session_file",
        "input_tokens", "output_tokens",
        "cache_read_tokens", "cache_creation_tokens",
        "total_tokens", "estimated_api_cost_usd"
    ]

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # Write JSON
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    # Print summary
    if args.summary and rows:
        # Group by date
        by_date = {}
        for r in rows:
            d = r["date"]
            if d not in by_date:
                by_date[d] = {
                    "sessions": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read_tokens": 0,
                    "cache_creation_tokens": 0,
                    "estimated_api_cost_usd": 0,
                }
            by_date[d]["sessions"] += 1
            by_date[d]["input_tokens"] += r["input_tokens"]
            by_date[d]["output_tokens"] += r["output_tokens"]
            by_date[d]["cache_read_tokens"] += r["cache_read_tokens"]
            by_date[d]["cache_creation_tokens"] += r["cache_creation_tokens"]
            by_date[d]["estimated_api_cost_usd"] += r["estimated_api_cost_usd"]

        print("\n=== Daily Summary ===")
        print(f"{'Date':<12} {'Sessions':>8} {'Input':>12} {'Output':>12} {'Cache Read':>14} {'Cache Create':>14} {'Cost':>10}")
        print("-" * 86)
        for d in sorted(by_date.keys(), reverse=True):
            s = by_date[d]
            print(f"{d:<12} {s['sessions']:>8} {s['input_tokens']:>12,} {s['output_tokens']:>12,} {s['cache_read_tokens']:>14,} {s['cache_creation_tokens']:>14,} ${s['estimated_api_cost_usd']:>8.2f}")
    else:
        daily_total = sum(r["total_tokens"] for r in rows)
        daily_cost = sum(r["estimated_api_cost_usd"] for r in rows)
        daily_input = sum(r["input_tokens"] for r in rows)
        daily_output = sum(r["output_tokens"] for r in rows)
        daily_cache_read = sum(r["cache_read_tokens"] for r in rows)
        daily_cache_create = sum(r["cache_creation_tokens"] for r in rows)

        print(f"\n=== Claude Code Usage Report ===")
        print(f"Date filter: {'all' if args.all else target_date}")
        print(f"Sessions: {len(rows)}")
        print(f"")
        print(f"  Input tokens:          {daily_input:>15,}")
        print(f"  Output tokens:         {daily_output:>15,}")
        print(f"  Cache read tokens:     {daily_cache_read:>15,}")
        print(f"  Cache creation tokens: {daily_cache_create:>15,}")
        print(f"  ─────────────────────────────────")
        print(f"  Total tokens:          {daily_total:>15,}")
        print(f"")
        print(f"  Estimated API cost:    ${daily_cost:>14.2f}")
        print(f"")
        print(f"Output files:")
        print(f"  CSV:  {CSV_PATH}")
        print(f"  JSON: {JSON_PATH}")


if __name__ == "__main__":
    main()
