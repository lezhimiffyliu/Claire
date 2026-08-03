#!/usr/bin/env python3
"""
UW Calculus Exam Scraper
========================
Scrapes Math 124, 125, 126 final exam PDFs from the UW Math Department website.

Downloads both question PDFs and solution/answer PDFs (when available).
Saves to: ../downloads/COURSE/TERM/
Creates: ../downloads/manifest.json

Usage:
  python scrape_uw_exams.py                  # download all three courses
  python scrape_uw_exams.py --course 124     # just Math 124
  python scrape_uw_exams.py --dry-run        # preview what would be downloaded
  python scrape_uw_exams.py --since 2022     # only exams from 2022 onwards
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent
BENCH_DIR    = SCRIPT_DIR.parents[2]  # repo root
DOWNLOAD_DIR = BENCH_DIR / "data" / "uw" / "raw"
MANIFEST     = DOWNLOAD_DIR / "manifest_125.json"

COURSES = {
    "124": {
        "archive_url": "https://sites.math.washington.edu/~m124/SampleFinal.php",
        "base_url":    "https://sites.math.washington.edu/~m124/SampleFinal.php",
        "name":        "Math 124",
    },
    "125": {
        "archive_url": "https://sites.math.washington.edu/~m125/Quizzes/Q10.php",
        "base_url":    "https://sites.math.washington.edu/~m125/Quizzes/Q10.php",
        "name":        "Math 125",
    },
    "126": {
        "archive_url": "https://sites.math.washington.edu/~m126/finals/final.php",
        "base_url":    "https://sites.math.washington.edu/~m126/finals/final.php",
        "name":        "Math 126",
    },
}

# Regex to extract year from filename for --since filtering
YEAR_RE = re.compile(r"(20\d{2}|[AaWwSs][pu]?\d{2})")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; UW-Calculus-Scraper/1.0; "
        "educational research tool)"
    )
}

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_base_url(html: str, page_url: str) -> str:
    """Extract <base href> from HTML if present, otherwise use page URL as base."""
    m = re.search(r'<base\s+href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if m:
        return urljoin(page_url, m.group(1))
    return page_url


def extract_pdf_links(html: str, base_url: str) -> list[dict]:
    """
    Find all PDF hrefs, resolve to absolute URLs, classify as question/solution.
    Returns list of {url, filename, is_solution}.
    """
    pattern = re.compile(r'href="([^"]*\.pdf)"', re.IGNORECASE)
    seen = set()
    results = []

    for match in pattern.finditer(html):
        href = match.group(1)
        abs_url = urljoin(base_url, href)

        if abs_url in seen:
            continue
        seen.add(abs_url)

        filename = Path(urlparse(abs_url).path).name
        # Classify as solution if filename contains sol/ans/answer
        is_solution = bool(re.search(r"(sol|ans|answer)", filename, re.IGNORECASE))

        results.append({
            "url":         abs_url,
            "filename":    filename,
            "is_solution": is_solution,
        })

    return results


def extract_year(filename: str) -> int | None:
    """Try to extract a 4-digit year from filename (e.g. Au25 → 2025, 2024 → 2024)."""
    # Direct 4-digit year
    m = re.search(r"20(\d{2})", filename)
    if m:
        return 2000 + int(m.group(1))
    # 2-digit year suffix like Au25, W25, Sp23
    m = re.search(r"[AaWwSs][pu]?(\d{2})", filename)
    if m:
        return 2000 + int(m.group(1))
    return None


def term_from_filename(filename: str) -> str:
    """Best-effort term label from filename."""
    f = filename.lower()
    if "au" in f or "aut" in f:
        season = "Autumn"
    elif "wi" in f or "win" in f:
        season = "Winter"
    elif "sp" in f or "spr" in f:
        season = "Spring"
    elif "su" in f or "sum" in f:
        season = "Summer"
    else:
        season = "Unknown"
    year = extract_year(filename)
    return f"{season} {year}" if year else season


def download_file(url: str, dest: Path) -> bool:
    """Download url to dest. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as resp:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"  ⚠️  Failed to download {url}: {e}", file=sys.stderr)
        return False


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {"exams": {}}


def save_manifest(manifest: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def scrape_course(course_id: str, cfg: dict, since: int | None, dry_run: bool,
                  manifest: dict) -> int:
    print(f"\n{'='*60}")
    print(f"  {cfg['name']} — {cfg['archive_url']}")
    print(f"{'='*60}")

    html      = fetch_html(cfg["archive_url"])
    base_url  = get_base_url(html, cfg["archive_url"])
    all_links = extract_pdf_links(html, base_url)

    # Separate questions from solutions
    questions = [l for l in all_links if not l["is_solution"]]
    solutions = {l["filename"]: l for l in all_links if l["is_solution"]}

    print(f"Found {len(questions)} question PDFs, {len(solutions)} solution PDFs")

    downloaded = 0

    for q in questions:
        year = extract_year(q["filename"])
        if since and year and year < since:
            continue

        term     = term_from_filename(q["filename"])
        exam_key = f"uw_{course_id}_{q['filename'].replace('.pdf','').lower()}"

        # Find matching solution
        sol = None
        # Try common suffixes
        base = re.sub(r'\.pdf$', '', q["filename"], flags=re.IGNORECASE)
        for suffix in ["_sol", "_ans", "_answer", "Sol", "Ans"]:
            candidate = base + suffix + ".pdf"
            if candidate in solutions:
                sol = solutions[candidate]
                break
            # case-insensitive search
            for sname, sdata in solutions.items():
                if sname.lower() == candidate.lower():
                    sol = sdata
                    break
            if sol:
                break

        q_dest = DOWNLOAD_DIR / f"math{course_id}" / q["filename"]
        s_dest = (DOWNLOAD_DIR / f"math{course_id}" / sol["filename"]) if sol else None

        # Check if already downloaded
        q_exists = q_dest.exists()
        s_exists = s_dest.exists() if s_dest else True  # no sol = no need to re-dl

        status_icon = "✅" if (q_exists and s_exists) else "📥"
        sol_info = f" + {sol['filename']}" if sol else " (no solution found)"
        print(f"  {status_icon} {q['filename']}{sol_info}  [{term}]")

        if dry_run:
            continue

        # Download question PDF
        if not q_exists:
            ok = download_file(q["url"], q_dest)
            if ok:
                downloaded += 1
                print(f"     → Downloaded: {q_dest.name}")
            time.sleep(0.3)  # be polite
        
        # Download solution PDF
        if sol and s_dest and not s_dest.exists():
            ok = download_file(sol["url"], s_dest)
            if ok:
                downloaded += 1
                print(f"     → Downloaded: {s_dest.name}")
            time.sleep(0.3)

        # Update manifest
        if not dry_run:
            manifest["exams"][exam_key] = {
                "course":        cfg["name"],
                "term":          term,
                "exam_type":     "final",
                "question_pdf":  str(q_dest.relative_to(BENCH_DIR)) if q_dest.exists() else None,
                "solution_pdf":  str(s_dest.relative_to(BENCH_DIR)) if s_dest and s_dest.exists() else None,
                "source_url":    q["url"],
            }

    return downloaded


def main():
    parser = argparse.ArgumentParser(description="Scrape UW Calculus past exam PDFs")
    parser.add_argument("--course", choices=["124", "125", "126"],
                        help="Scrape only this course (default: all)")
    parser.add_argument("--since", type=int, metavar="YEAR",
                        help="Only download exams from this year onwards (e.g. 2022)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without downloading")
    args = parser.parse_args()

    if args.dry_run:
        print("🔍 DRY RUN — nothing will be downloaded\n")

    manifest = load_manifest()
    courses  = {args.course: COURSES[args.course]} if args.course else COURSES
    total    = 0

    for course_id, cfg in courses.items():
        total += scrape_course(course_id, cfg, args.since, args.dry_run, manifest)

    if not args.dry_run:
        save_manifest(manifest)
        print(f"\n✅ Done. {total} new file(s) downloaded.")
        print(f"📋 Manifest: {MANIFEST}")
    else:
        print("\n[dry-run complete]")


if __name__ == "__main__":
    main()
