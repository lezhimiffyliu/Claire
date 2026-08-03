#!/usr/bin/env python3
"""
UW Math 126 extractor — Claude Haiku (VLM), with auto diagram cropping + Supabase upload.

Usage:
  python extract_126.py --exam Au24
  python extract_126.py --exam Sp24 --api-key sk-ant-...
"""

import argparse, base64, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

import anthropic
from PIL import Image

SCRIPT_DIR     = Path(__file__).parent
BENCH_DIR      = SCRIPT_DIR.parents[2]  # repo root
DOWNLOAD_DIR   = BENCH_DIR / "data" / "uw" / "raw" / "math126"
OUTPUT_DIR     = BENCH_DIR / "data" / "uw" / "processed" / "math126"
MODEL          = "claude-haiku-4-5"
SUPABASE_URL   = "https://jesfegjblkddopcyqyfc.supabase.co"
STORAGE_BUCKET = "materials"


def normalize_stem(raw: str) -> tuple[str, str]:
    """
    Normalize exam stem to Au24/Sp24/Wi24 format.
    Returns (normalized_stem, label).
    """
    raw_lower = raw.lower()

    # Extract year (2 or 4 digits)
    year_match = re.search(r'(\d{2,4})', raw)
    if not year_match:
        return raw, raw
    year = year_match.group(1)
    if len(year) == 4:
        year = year[2:]  # 2024 -> 24

    # Determine season
    if 'au' in raw_lower or 'aut' in raw_lower:
        return f"Au{year}", f"Autumn 20{year}"
    elif 'sp' in raw_lower or 'spr' in raw_lower:
        return f"Sp{year}", f"Spring 20{year}"
    elif 'wi' in raw_lower or 'win' in raw_lower or raw_lower.startswith('w'):
        return f"Wi{year}", f"Winter 20{year}"
    elif 'su' in raw_lower or 'sum' in raw_lower:
        return f"Su{year}", f"Summer 20{year}"
    else:
        return f"{raw[:2].title()}{year}", f"20{year}"


def load_exam_map() -> dict:
    """Scan download directory for available exams."""
    exam_map = {}

    if not DOWNLOAD_DIR.exists():
        return exam_map

    # Find all question PDFs (not answer/solution PDFs)
    for pdf in DOWNLOAD_DIR.glob("*.pdf"):
        name = pdf.name.lower()
        if 'ans' in name or 'sol' in name:
            continue

        # Extract term from filename: m126finalSpr2025.pdf, m126finalAut2024.pdf
        m = re.search(r'm?126final([a-z]+\d+)\.pdf', name, re.IGNORECASE)
        if not m:
            continue

        raw_stem = m.group(1)
        stem, label = normalize_stem(raw_stem)

        # Find matching answer PDF
        base = pdf.stem
        ans_pdf = None
        for suffix in ['Ans', 'ans', 'Sol', 'sol', '_ans', '_sol']:
            candidate = DOWNLOAD_DIR / f"{base}{suffix}.pdf"
            if candidate.exists():
                ans_pdf = candidate.name
                break

        exam_map[stem] = (pdf.name, ans_pdf, label)

    return exam_map


EXAM_MAP = load_exam_map()

# ─── Helpers ──────────────────────────────────────────────────────────────────

def pdf_to_images(pdf_path: Path, out_dir: Path, prefix: str) -> list[Path]:
    """Convert PDF to PNG images. Output: prefix-01.png, prefix-02.png, etc."""
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
1. Copy question text VERBATIM. Do NOT summarize, paraphrase, or omit anything. If a problem defines a function (e.g., "Let f(x) = ..."), this MUST be included in the stem. 
It is critical context for all parts and must never be omitted.
   - Include every checkbox/multiple-choice option with exact text
   - Include every fill-in-the-blank or "circle one" instruction
2. Math: use LaTeX ($...$ inline, $$...$$ display block).
3. points: read from exam header if printed. Never null if printed.
4. page_number: Use the [Page N] label number I provided, NOT the "Page X of Y" printed in the exam header. The [Page N] labels start from 1 for the first image.
5. stem: shared intro text before sub-parts, or null if none.
6. parts: if no sub-parts, use [{"label": null, "question_text": "...", ...}]
7. depends_on: set when a part says "Using your answer from (a)..." or similar.
8. has_diagram: true ONLY if a diagram/graph/figure/3D object is physically displayed next to or within that specific part. Do NOT set true just because the part references a diagram from a previous part or the stem. Only the FIRST part that introduces the diagram should have has_diagram=true.
9. diagram_page: if has_diagram=true, use the [Page N] label number where the diagram appears, NOT the printed "Page X of Y" header.
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
    - multivariable_optimization
    - double_integrals
    - polar_coordinates
    - applications_of_double_integrals
    - taylor_polynomials_and_series
12. concepts: array of snake_case strings from these subtopics:
    - vectors_and_geometry: three_dimensional_coordinate_system, vector_representation, vector_operations, magnitude_and_direction, dot_product, angle_between_vectors, orthogonality, vector_projection
    - lines_and_planes: parametric_equations_of_lines, symmetric_equations_of_lines, direction_vectors, equations_of_planes, normal_vector_to_plane, line_plane_intersection, parallel_and_perpendicular_conditions
    - quadric_surfaces: cylinders, elliptic_paraboloid, hyperbolic_paraboloid, ellipsoid, hyperboloid_of_one_sheet, hyperboloid_of_two_sheets, surface_identification, traces_of_surfaces
    - vector_valued_functions: vector_functions_definition, space_curves, component_functions, limits_of_vector_functions, derivatives_of_vector_functions, integrals_of_vector_functions, tangent_vector, parametrization_of_curves
    - motion_in_space: velocity_vector, speed, acceleration_vector, tangential_and_normal_components, arc_length_parameterization, curvature, normal_vector, binormal_vector, normal_plane
    - multivariable_functions: functions_of_two_variables, domain_in_r2, level_curves, level_surfaces, visualization_of_surfaces
    - partial_derivatives: partial_derivative_definition, higher_order_partial_derivatives, mixed_partials, clairs_theorem, implicit_partial_differentiation
    - tangent_planes_and_differentials: tangent_plane_equation, linear_approximation_multivariable, total_differential, differentials_interpretation
    - multivariable_optimization: critical_points_multivariable, second_derivative_test_multivariable, local_extrema_multivariable, global_extrema_multivariable, optimization_with_constraints, lagrange_multipliers
    - double_integrals: double_integrals_over_rectangles, double_integrals_over_general_regions, iterated_integrals, changing_order_of_integration, integration_bounds_setup
    - polar_coordinates: polar_coordinate_conversion, graphing_in_polar, area_in_polar_coordinates, polar_integral_setup
    - applications_of_double_integrals: mass_from_density_2d, center_of_mass_2d, moments_2d, average_value_multivariable
    - taylor_polynomials_and_series: first_order_taylor_polynomial, second_order_taylor_polynomial, higher_order_taylor_polynomial, taylor_series_definition, error_estimation_taylor, building_new_series_from_known_series, power_series_representation

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

Identify just the core diagram area — I will add 40px padding automatically. No other text."""

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
        # clamp to image bounds with padding
        PAD = 40
        x1, y1 = max(0, x1 - PAD), max(0, y1 - PAD)
        x2, y2 = min(w, x2 + PAD), min(h, y2 + PAD)
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

# ─── Process single exam ──────────────────────────────────────────────────────

def process_exam(stem: str, client, supabase_key: str | None, skip_upload: bool) -> bool:
    """Process a single exam. Returns True on success."""
    if stem not in EXAM_MAP:
        print(f"ERROR: Unknown exam '{stem}'", file=sys.stderr)
        return False

    q_name, a_name, label = EXAM_MAP[stem]
    q_pdf = DOWNLOAD_DIR / q_name
    a_pdf = DOWNLOAD_DIR / a_name if a_name else None

    if not q_pdf.exists():
        print(f"ERROR: {q_pdf} not found. Run scrape_uw_exams.py first.", file=sys.stderr)
        return False

    OUTPUT_DIR.mkdir(exist_ok=True)
    img_dir = OUTPUT_DIR / f"math126_{stem}_images"
    img_dir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Math 126 — {label} ({stem})")
    print(f"{'='*60}")

    # ── Step 1: PDF → images ──────────────────────────────────────
    # Question PDF → page-01.png, page-02.png (kept for diagram cropping)
    print("\n[1/5] Converting PDFs to images...")
    q_pages = pdf_to_images(q_pdf, img_dir, "page")
    print(f"      {len(q_pages)} question pages → page-01.png ... page-{len(q_pages):02d}.png")

    # Answer PDF → separate temp images (deleted after extraction)
    a_pages = []
    a_tmp_dir = None
    if a_pdf and a_pdf.exists():
        a_tmp_dir = img_dir / "_ans_tmp"
        a_tmp_dir.mkdir(exist_ok=True)
        a_pages = pdf_to_images(a_pdf, a_tmp_dir, "ans")
        print(f"      {len(a_pages)} answer pages (temp, will be deleted)")

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
        # Clean up temp answer images
        if a_tmp_dir and a_tmp_dir.exists():
            shutil.rmtree(a_tmp_dir)
            print(f"      Cleaned up temp answer images")
    else:
        print("\n[3/5] No answer PDF found, skipping answer extraction")

    # ── Step 4: Crop diagrams with LLM-detected bbox ─────────────
    # Use Claude to detect diagram bbox (x1, y1, x2, y2) and crop with padding=40
    print("\n[4/5] Cropping diagrams with LLM bbox detection...")
    diagrams_dir = img_dir / "diagrams"
    diagrams_dir.mkdir(exist_ok=True)

    for p in problems:
        for part in p.get("parts", []):
            if not part.get("has_diagram"):
                continue

            # Get diagram page from the part (not the problem)
            diag_page = part.get("diagram_page")
            if not diag_page or diag_page < 1 or diag_page > len(q_pages):
                print(f"      ⚠️  P{p['problem_number']} part={part.get('label')}: diagram_page {diag_page} out of range")
                continue

            # diagram_page uses [Page N] labels starting from 1, but q_pages is 0-indexed
            # [Page 1] → q_pages[0], [Page 4] → q_pages[3]
            page_img = q_pages[diag_page - 1]

            # Generate crop filename: p1_a.png, p2.png, etc.
            crop_filename = f"p{p['problem_number']}"
            if part.get('label'):
                crop_filename += f"_{part['label']}"
            crop_filename += ".png"
            crop_path = diagrams_dir / crop_filename

            # Crop diagram using LLM bbox detection
            if crop_diagram(client, page_img, diag_page, p['problem_number'], part.get('label'), crop_path):
                part["diagram_image_local"] = str(crop_path.relative_to(BENCH_DIR))
            else:
                # Fallback to full page if cropping fails
                print(f"      📄 Fallback to full page: {page_img.name}")
                part["diagram_image_local"] = str(page_img.relative_to(BENCH_DIR))

    # ── Step 5: Upload to Supabase ────────────────────────────────
    if not skip_upload and supabase_key:
        print("\n[5/5] Uploading to Supabase...")
        sb_prefix = f"math126/{stem}"

        # Upload question PDF
        q_url = upload_to_supabase(supabase_key, q_pdf, f"{sb_prefix}/{q_name}")
        print(f"      ✅ PDF: {q_url}")

        # Upload answer PDF
        if a_pdf and a_pdf.exists():
            a_url = upload_to_supabase(supabase_key, a_pdf, f"{sb_prefix}/{a_name}")
            print(f"      ✅ Ans PDF: {a_url}")

        # Upload diagram crops
        for p in problems:
            for part in p.get("parts", []):
                local = part.get("diagram_image_local")
                if not local:
                    continue
                crop_path = BENCH_DIR / local
                crop_sb = f"{sb_prefix}/diagrams/{crop_path.name}"
                url = upload_to_supabase(supabase_key, crop_path, crop_sb)
                part["diagram_image_url"] = url
                print(f"      ✅ Diagram: {url}")
    elif skip_upload:
        print("\n[5/5] Skipping Supabase upload (--skip-upload)")
    else:
        print("\n[5/5] No SUPABASE_SERVICE_KEY — skipping upload")

    # ── Save output ───────────────────────────────────────────────
    out_stem = f"math126_{stem}"
    json_path = OUTPUT_DIR / f"{out_stem}.json"
    md_path   = OUTPUT_DIR / f"{out_stem}.md"

    json_path.write_text(json.dumps(problems, indent=2, ensure_ascii=False))
    md_path.write_text(to_markdown(problems, label))

    # Copy to problems/ for Claire to load
    problems_dir = BENCH_DIR / "backend" / "problems"
    problems_dir.mkdir(exist_ok=True)
    shutil.copy(json_path, problems_dir / json_path.name)

    print(f"\n{'='*60}")
    print(f"  ✅ Done!")
    print(f"  JSON: {json_path}")
    print(f"  → Copied to: {problems_dir / json_path.name}")
    print(f"  MD:   {md_path}")
    print(f"  Images: {img_dir}")
    print(f"{'='*60}\n")
    return True

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exam", help="e.g. Spr2025")
    parser.add_argument("--all", action="store_true", help="Process all available exams")
    parser.add_argument("--list-exams", action="store_true", help="List available exams")
    parser.add_argument("--api-key", default=os.environ.get("ANTHROPIC_API_KEY"))
    parser.add_argument("--supabase-key", default=os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
    parser.add_argument("--skip-upload", action="store_true", help="Skip Supabase upload")
    args = parser.parse_args()

    if args.list_exams:
        print("\nAvailable Math 126 exams:")
        for stem, (q_name, a_name, label) in sorted(EXAM_MAP.items()):
            has_ans = "✅" if a_name else "❌"
            print(f"  {stem:12} → {label:20} (answers: {has_ans})")
        print(f"\nTotal: {len(EXAM_MAP)} exams")
        return

    if not args.exam and not args.all:
        print("ERROR: --exam or --all required (or use --list-exams)", file=sys.stderr)
        sys.exit(1)

    if not args.api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=args.api_key)

    if args.all:
        # Process all exams
        exams = sorted(EXAM_MAP.keys())
        print(f"\n🚀 Processing {len(exams)} exams...")
        success, failed = 0, 0
        for i, stem in enumerate(exams, 1):
            print(f"\n[{i}/{len(exams)}] Processing {stem}...")
            try:
                if process_exam(stem, client, args.supabase_key, args.skip_upload):
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                failed += 1
        print(f"\n{'='*60}")
        print(f"  📊 Summary: {success} succeeded, {failed} failed")
        print(f"{'='*60}\n")
    else:
        # Process single exam
        if not process_exam(args.exam, client, args.supabase_key, args.skip_upload):
            sys.exit(1)


if __name__ == "__main__":
    main()
