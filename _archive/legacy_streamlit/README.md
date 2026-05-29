# Legacy Streamlit App

These files are kept temporarily for reference only.

## Archived Files
- app.py: main Streamlit application (replaced by api.py + web/)
- app_legacy.py: older Streamlit version
- main.py: CLI entry point
- exam_parser.py: PDF parsing (used only by app_legacy.py)
- exam_panic.py: exam prep logic (replaced by roadmap_generator.py)
- pages/upload.py: Streamlit multi-page upload

## Current Architecture
- Backend: `api.py` (FastAPI)
- Frontend: `web/` (Vite + React)

Do not import these files from active code.
Delete after confirming the new architecture is stable.
