#!/usr/bin/env python3
"""
UW Math 126 extractor — Claude Haiku (VLM), with auto diagram cropping + Supabase upload.

Usage:
  python extract_126.py --exam Spr2025
  python extract_126.py --exam Spr2025 --api-key sk-ant-...
"""

import argparse, base64, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

import anthropic
from PIL import Image

SCRIPT_DIR     = Path(__file__).parent
BENCH_DIR      = SCRIPT_DIR.parent
DOWNLOAD_DIR   = BENCH_DIR / "uw_data"/ "downloads" / "math126"
OUTPUT_DIR     = BENCH_DIR / "uw_data"
MODEL          = "claude-haiku-4-5"
SUPABASE_URL   = "https://jesfegjblkddopcyqyfc.supabase.co"
STORAGE_BUCKET = "materials"

EXAM_MAP = {
    # stem → (question_pdf_name, answer_pdf_name, label)
    "Spr2025": ("m126finalSpr2025.pdf", "m126finalSpr2025Ans.pdf", "Spring 2025"),
    "Win2025": ("m126finalWin2025.pdf", "m126finalWin2025Ans.pdf", "Winter 2025"),
    "Aut2024": ("m126finalAut2024.pdf", "m126finalAut2024Ans.pdf", "Autumn 2024"),
    "Spr2024": ("m126finalSpr2024.pdf", "m126finalSpr2024Ans.pdf", "Spring 2024"),
    "Win2024": ("m126finalWin2024.pdf", "m126finalWin2024Ans.pdf", "Winter 2024"),
    "Aut2023": ("m126finalAut2023.pdf", "m126finalAut2023Ans.pdf", "Autumn 2023"),
    "Spr2023": ("m126finalSpr2023.pdf", "m126finalSpr2023Ans.pdf", "Spring 2023"),
    "Win2023": ("m126finalWin2023.pdf", "m126finalWin2023Ans.pdf", "Winter 2023"),
    "Aut2022": ("m126finalAut2022.pdf", "m126finalAut2022Ans.pdf", "Autumn 2022"),
    "Win2022": ("m126finalWin2022.pdf", "m126finalWin2022Ans.pdf", "Winter 2022"),
    "Aut2021": ("m126finalAut2021.pdf", "m126finalAut2021Ans.pdf", "Autumn 2021"),
    "Spr2019": ("m126finalSpr2019.pdf", "m126finalSpr2019Ans.pdf", "Spring 2019"),
    "Win2019": ("m126finalWin2019.pdf", "m126finalWin2019Ans.pdf", "Winter 2019"),
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def pdf_to_images(pdf_path: Path, out_dir: Path, prefix: str) -> list[Path]:
    subprocess.run(
        ["pdftoppm", "-r", "150", "-png", str(pdf_path), str(out_dir / prefix)],
        check=True, capture_output=True
    )
    return sorted(out_dir.glob(f"{prefix}-*.png"))

def encode(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode()

def image_block(path: Path) -> dict:
    return {"type": "image", "source": {
        "type": "base64", "media_type": "image/png", "data": encode(path)
    }}

def call_claude(client, pages: list[Path], prompt: str) -> list:
    content = []
    for i, p in enumerate(pages, 1):
        content.append({"type": "text", "text": f"[Page {i}]"})
        content.append(image_block(p))
    content.append({"type": "text", "text": prompt})
    resp = client.messages.create(
        model=MODEL, max_tokens=8192,
        messages=[{"role": "user", "content": content}]
    )
    raw = resp.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)

def upload_to_supabase(service_key: str, local_path: Path, storage_path: str) -> str:
    """Upload file to Supabase Storage using requests (HTTP/1.1)."""
    import requests
    mime = "application/pdf" if local_path.suffix == ".pdf" else "image/png"
    url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{storage_path}"
    headers = {
        "Authorization": f"Bearer {service_key}",
        "Content-Type": mime,
        "x-upsert": "true",
    }
    with open(local_path, "rb") as f:
        resp = requests.post(url, headers=headers, data=f)
    if resp.status_code not in (200, 201):
        raise Exception(f"Upload failed: {resp.status_code} {resp.text}")
    return f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{storage_path}"

# ─── Prompts ──────────────────────────────────────────────────────────────────

QUESTION_PROMPT = """Extract every problem from this UW Math 126 (Calculus III) final exam. Return a JSON array.

Math 126 covers: vectors and geometry in 3D space, lines and planes, dot/cross products, vector-valued functions, arc length, curvature, multivariable functions, partial derivatives, tangent planes, gradient, directional derivatives, optimization (critical points, Lagrange multipliers), double and triple integrals, coordinate systems (polar, cylindrical, spherical), vector fields, line integrals, Green's theorem, Taylor series, and sequences/series (if included).

CRITICAL RULES — follow exactly:
1. Copy question text VERBATIM. Do NOT summarize, paraphrase, or omit anything.
   - Include every checkbox/multiple-choice option with exact text
   - Include every fill-in-the-blank or "circle one" instruction
2. Math: use LaTeX ($...$ inline, $$...$$ display block).
3. points: read from exam header if printed. Never null if printed.
4. page_number: 1-indexed page where this problem starts (match [Page N] labels).
5. stem: shared intro text before sub-parts, or null if none.
6. parts: if no sub-parts, use [{"label": null, "question_text": "...", ...}]
7. depends_on: set when a part says "Using your answer from (a)..." or similar.
8. has_diagram: true only if that specific part shows or references a graph/figure/diagram/3D object/shaded region.
9. diagram_page: if has_diagram=true, the [Page N] number where the diagram appears.
10. diagram_description: if has_diagram=true, describe in full detail — type (graph, 3D surface, region, vector field, etc.), axes labels and ranges, curves/surfaces drawn, shaded regions, key labeled points, all annotations. Enough for a student to reconstruct it. null if no diagram.
11. topic: MUST be one of these exact values:
    - vectors_and_geometry
    - lines_and_planes
    - quadric_surfaces
    - vector_valued_functions
    - motion_in_space
    - multivariable_functions
    - partial_derivatives
    - tangent_planes_and_differentials
    - multivariable_optimization (includes Lagrange multipliers)
    - double_integrals
    - polar_coordinates
    - applications_of_double_integrals (center of mass, moments)
    - taylor_polynomials_and_series
12. concepts: array of snake_case strings (finer-grained subtopics).

Schema:
[
  {
    "problem_number": 3,
    "page_number": 4,
    "points": 10,
    "topic": "double_integrals",
    "concepts": ["double_integrals", "polar_coordinates", "area"],
    "stem": null,
    "parts": [
      {
        "label": "a",
        "question_text": "Set up but do not evaluate the integral...",
        "depends_on": null,
        "has_diagram": true,
        "diagram_page": 4,
        "diagram_description": "A shaded region R bounded by the circle r=2 and the line y=x in the first quadrant. The x-axis is labeled from 0 to 2, y-axis from 0 to 2. The region is shaded between the two curves.",
        "diagram_bbox": null
      }
    ]
  }
]

Return JSON array only. No other text."""

SOLUTION_PROMPT = """Extract final answers from this UW Math 126 solution/answer key. May be handwritten.

CRITICAL: Copy answers VERBATIM. Do NOT simplify or rephrase.
- Include all equivalent forms if shown (e.g. "$3\\sqrt{5} = \\sqrt{45}$")
- Math expressions: LaTeX ($...$ inline, $$...$$ display)
- Word answers: copy exact words ("Converges", "Diverges", "saddle point", etc.)

Return a JSON array, one entry per problem+part:
[
  {"problem_number": 1, "label": "a", "final_answer": "$\\\\frac{\\\\pi}{4}$"},
  {"problem_number": 2, "label": null, "final_answer": "Diverges"}
]

Return JSON array only. No other text."""

BBOX_PROMPT = """This is page {page_num} of a UW Math 126 (Calculus III) exam.
There is a diagram/figure/graph on this page for Problem {prob_num}{part_str}.

Identify the bounding box of the diagram (the box tightly enclosing the figure, not the surrounding text).
The image dimensions are {width}x{height} pixels.

Return JSON only:
{{"x1": <left pixel>, "y1": <top pixel>, "x2": <right pixel>, "y2": <bottom pixel>}}

Be generous — include a 10-20px margin around the diagram. No other text."""

# ─── Diagram cropping ─────────────────────────────────────────────────────────

def crop_diagram(client, page_img: Path, page_num: int, prob_num, part_label, out_path: Path) -> bool:
    """Ask Claude for diagram bbox, then crop with PIL. Returns True on success."""
    img = Image.open(page_img)
    w, h = img.size
    part_str = f" part ({part_label})" if part_label else ""
    prompt = BBOX_PROMPT.format(page_num=page_num, prob_num=prob_num,
                                 part_str=part_str, width=w, height=h)
    content = [image_block(page_img), {"type": "text", "text": prompt}]
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=256,
            messages=[{"role": "user", "content": content}]
        )
        raw = resp.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        bbox = json.loads(raw)
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
        # clamp to image bounds
        x1, y1 = max(0, x1-15), max(0, y1-15)
        x2, y2 = min(w, x2+15), min(h, y2+15)
        cropped = img.crop((x1, y1, x2, y2))
        cropped.save(out_path, "PNG")
        print(f"      ✂️  Cropped diagram → {out_path.name} ({x1},{y1})-({x2},{y2})")
        return True
    except Exception as e:
        print(f"      ⚠️  Crop failed: {e}")
        return False

# ─── Markdown generation ──────────────────────────────────────────────────────

def to_markdown(problems: list, exam_label: str, course: str = "Math 126") -> str:
    lines = [f"# {course} Final Exam — {exam_label}\n"]
    for p in problems:
        pts = f" ({p['points']} pts)" if p.get('points') else ""
        lines.append(f"## Problem {p['problem_number']}{pts}")
        lines.append(f"**Topic:** {p.get('topic', 'unknown')}  ")
        concepts = ", ".join(p.get("concepts", []))
        if concepts:
            lines.append(f"**Concepts:** {concepts}  ")
        if p.get("stem"):
            lines.append(f"\n{p['stem']}\n")
        for part in p.get("parts", []):
            part_label_str = part["label"] if part["label"] else ""
            label = f"**({part_label_str})**" if part["label"] else ""
            lines.append(f"\n{label} {part['question_text']}")
            if part.get("has_diagram") and part.get("diagram_description"):
                lines.append(f"\n> 📊 **Diagram:** {part['diagram_description']}")
            if part.get("diagram_image_url"):
                lines.append(f"\n> ![diagram]({part['diagram_image_url']})")
            ans = part.get("final_answer")
            if ans:
                lines.append(f"\n**Answer:** {ans}")
        lines.append("")
    return "\n".join(lines)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exam", required=True, help="e.g. Spr2025")
    parser.add_argument("--api-key", default=os.environ.get("ANTHROPIC_API_KEY"))
    parser.add_argument("--supabase-key", default=os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
    parser.add_argument("--skip-upload", action="store_true", help="Skip Supabase upload")
    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr); sys.exit(1)

    stem = args.exam
    if stem not in EXAM_MAP:
        print(f"ERROR: Unknown exam '{stem}'. Known: {list(EXAM_MAP.keys())}", file=sys.stderr)
        sys.exit(1)

    q_name, a_name, label = EXAM_MAP[stem]
    q_pdf = DOWNLOAD_DIR / q_name
    a_pdf = DOWNLOAD_DIR / a_name if a_name else None

    if not q_pdf.exists():
        print(f"ERROR: {q_pdf} not found. Run scrape_uw_exams.py first.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=args.api_key)
    OUTPUT_DIR.mkdir(exist_ok=True)

    img_dir = OUTPUT_DIR / f"math126_{stem}_images"
    img_dir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Math 126 — {label} ({stem})")
    print(f"{'='*60}")

    # ── Step 1: PDF → images ──────────────────────────────────────
    print("\n[1/5] Converting PDFs to images...")
    q_pages = pdf_to_images(q_pdf, img_dir, "q")
    print(f"      {len(q_pages)} question pages")
    a_pages = []
    if a_pdf and a_pdf.exists():
        a_pages = pdf_to_images(a_pdf, img_dir, "a")
        print(f"      {len(a_pages)} answer pages")

    # ── Step 2: Extract questions ─────────────────────────────────
    print("\n[2/5] Extracting questions via Claude VLM...")
    problems = call_claude(client, q_pages, QUESTION_PROMPT)
    print(f"      {len(problems)} problems extracted")

    # ── Step 3: Extract answers ───────────────────────────────────
    answers_map = {}
    if a_pages:
        print("\n[3/5] Extracting answers via Claude VLM...")
        raw_answers = call_claude(client, a_pages, SOLUTION_PROMPT)
        for a in raw_answers:
            key = (a["problem_number"], a.get("label"))
            answers_map[key] = a.get("final_answer")
        print(f"      {len(answers_map)} answers extracted")
        # Merge answers into problems
        for p in problems:
            for part in p.get("parts", []):
                k = (p["problem_number"], part.get("label"))
                if k in answers_map:
                    part["final_answer"] = answers_map[k]
    else:
        print("\n[3/5] No answer PDF found, skipping answer extraction")

    # ── Step 4: Crop diagrams ─────────────────────────────────────
    print("\n[4/5] Auto-cropping diagrams...")
    for p in problems:
        for part in p.get("parts", []):
            if not part.get("has_diagram"):
                continue
            diag_page = part.get("diagram_page") or p.get("page_number")
            if not diag_page or diag_page > len(q_pages):
                print(f"      ⚠️  P{p['problem_number']} part={part.get('label')}: page {diag_page} out of range")
                continue
            page_img = q_pages[diag_page - 1]
            crop_name = f"diag_p{p['problem_number']}_{part.get('label') or 'main'}.png"
            crop_path = img_dir / crop_name
            ok = crop_diagram(client, page_img, diag_page,
                              p["problem_number"], part.get("label"), crop_path)
            if ok:
                part["diagram_image_local"] = str(crop_path.relative_to(BENCH_DIR))

    # ── Step 5: Upload to Supabase ────────────────────────────────
    if not args.skip_upload and args.supabase_key:
        print("\n[5/5] Uploading to Supabase...")
        sb_prefix = f"math126/{stem}"

        # Upload question PDF
        q_url = upload_to_supabase(args.supabase_key, q_pdf, f"{sb_prefix}/{q_name}")
        print(f"      ✅ PDF: {q_url}")

        # Upload answer PDF
        if a_pdf and a_pdf.exists():
            a_url = upload_to_supabase(args.supabase_key, a_pdf, f"{sb_prefix}/{a_name}")
            print(f"      ✅ Ans PDF: {a_url}")

        # Upload diagram crops
        for p in problems:
            for part in p.get("parts", []):
                local = part.get("diagram_image_local")
                if not local:
                    continue
                crop_path = BENCH_DIR / local
                crop_sb = f"{sb_prefix}/diagrams/{crop_path.name}"
                url = upload_to_supabase(args.supabase_key, crop_path, crop_sb)
                part["diagram_image_url"] = url
                print(f"      ✅ Diagram: {url}")
    elif args.skip_upload:
        print("\n[5/5] Skipping Supabase upload (--skip-upload)")
    else:
        print("\n[5/5] No SUPABASE_SERVICE_KEY — skipping upload")

    # ── Save output ───────────────────────────────────────────────
    out_stem = f"math126_{stem}"
    json_path = OUTPUT_DIR / f"{out_stem}.json"
    md_path   = OUTPUT_DIR / f"{out_stem}.md"

    # Add metadata fields
    for p in problems:
        p["id"]     = f"uw_math_126_{stem.lower()}_p{p['problem_number']}"
        p["course"] = "math_126"
        p["exam"]   = f"{stem.lower()}_final"

    json_path.write_text(json.dumps(problems, indent=2, ensure_ascii=False))
    md_path.write_text(to_markdown(problems, label))

    print(f"\n{'='*60}")
    print(f"  ✅ Done!")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")
    print(f"  Images: {img_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
