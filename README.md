# ApplyMate AI — React + Django (MVP)

A resume-worthy, full-stack project that helps you track job postings and generate tailored application materials with AI.

## Quickstart

### 1) Backend (Django + DRF)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # set AI_API_KEY if you have one
python manage.py migrate
python manage.py runserver
```

This serves the API at `http://127.0.0.1:8000/api/` and media files at `http://127.0.0.1:8000/media/` (in DEBUG).

### 2) Frontend (Vite + React)

```bash
cd ../frontend
cp .env.example .env  # ensure VITE_API_BASE points to your backend /api
npm install
npm run dev
```

Open the printed local URL (usually `http://127.0.0.1:5173`).

## Features implemented in this MVP

- **Add Job** from URL or pasted JD text. Basic extraction using either OpenAI (if configured) or a rule-based fallback.
- **Fit Score** by comparing JD keywords vs your resume text.
- **Tailored Docs** generation (bullets + cover letter) with a simple template fallback; one click **DOCX export**.
- **Pipeline**: create applications and move between stages.
- **Dashboard**: basic bar chart of stage counts.

## Notes

- Upload resumes in **Settings** (`.docx` or `.pdf`). Text is parsed server-side for AI.
- If no `AI_API_KEY` is set, the app falls back to simple, deterministic logic so you can demo it offline.
- Generated DOCX files are saved under `backend/media/generated/` and exposed at `/media/generated/...` in DEBUG mode.

## Next steps (suggested)

- Auth (JWT), multi-user support, and user-specific data.
- Better JD parsing using a robust schema (Pydantic) + better skill extraction.
- Interview prep Q&A and RAG using embeddings (e.g., store chunks in Postgres or SQLite FTS).
- Kanban with drag & drop (react-beautiful-dnd).
- Email helper + ICS file downloads for follow-ups.

---

Built on 2025-08-21.
