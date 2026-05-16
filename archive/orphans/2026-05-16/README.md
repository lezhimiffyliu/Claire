# Archived Orphan Files - 2026-05-16

## Why Archived
These files had **0 imports** across the entire codebase. They are not used by any active code and were identified during a repository structure audit.

## Files

| File | Original Path | Reason |
|------|---------------|--------|
| `exam_analyzer.py` | `/exam_analyzer.py` | Replaced by `exam_context.py` |
| `knowledge_loader.py` | `/knowledge_loader.py` | Stub code, never implemented |
| `profile_summary.py` | `/profile_summary.py` | Logic exists in `student_profile_v2.py` |
| `profile_updater.py` | `/profile_updater.py` | Merged into `student_profile.py` |
| `sympy_backup.py` | `/sympy_backup.py` | Obsolete backup, use `sympy_tools.py` |

## Verification Method
```bash
grep -r "from <module>\|import <module>" . --include="*.py" | grep -v ".pyc"
# Result: 0 matches for each file
```

## How to Restore
If you need to restore any file:
```bash
git mv archive/orphans/2026-05-16/<filename>.py ./<filename>.py
```

## Note
`teaching_tools.py` was listed as orphan but not found on disk (may have been deleted earlier).
