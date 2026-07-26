# UW exam dataset

Source/reference data for Claire's problem bank: real University of Washington
Math 124 / 125 / 126 past exams.

## Layout

```
data/uw/
├── raw/         # RAW source: exam PDFs scraped from UW (question + solution PDFs)
│   ├── math124/ math125/ math126/
│   └── manifest_*.json
└── processed/   # GENERATED: per-exam page/diagram images + extracted problem JSON
    ├── math124/ math125/ math126/
    └── ...
```

- **raw/** — original downloaded PDFs. Not regenerable except by re-scraping UW.
- **processed/** — generated from `raw/` by the extraction pipeline (page renders,
  cropped diagrams, and structured problem JSON). Regenerable from `raw/`.

## Which scripts consume / produce it

`scripts/data/uw/` (the offline data pipeline, not part of the running app):

- `scrape_uw_exams.py` → downloads PDFs into `raw/`.
- `extract_124.py` / `extract_125.py` / `extract_126.py` → read `raw/`, render
  images + call an LLM to extract problems, write to `processed/`, and copy the
  final problem JSON into `backend/problems/` (which the app's
  `app/content/problem_loader.py` loads at runtime).

The **running application does not read this directory** — it reads the curated
JSON in `backend/problems/`. This dataset is only needed to (re)generate that JSON.

## Why it's excluded from git

~209 MB of PDFs and images — too large for git. `raw/` and `processed/` are
gitignored (see `.gitignore`); only this README is tracked. Regenerate `processed/`
from `raw/` with the extraction scripts; re-obtain `raw/` via `scrape_uw_exams.py`.
