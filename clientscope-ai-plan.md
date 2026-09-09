# ClientScope AI — Build Plan

Portfolio project for freelancers. Turns messy client material (PDFs, DOCX, screenshots,
pasted chat/email) into a structured, autonomous project specification.

Build order: **backend first → React frontend**. This doc is the spec to feed Claude Code
(via `/plan`, `/goals`, or just pasted as context) so every session stays aligned to the
same architecture instead of drifting.

---

## 1. Goals

- [ ] Accept PDF, DOCX, screenshot (image), and pasted text as input
- [ ] Normalize all input types into one unified text+image representation
- [ ] Run a multi-agent LangGraph pipeline that extracts goals, features, unknowns, risks,
      a complexity score, and follow-up questions
- [ ] Enforce structured output (Pydantic schema) — no hand-parsed JSON
- [ ] Persist project specs and version history in a database
- [ ] Support a feedback loop: client answers a follow-up question → spec updates in place
- [ ] Expose a clean REST API for the React frontend to consume
- [ ] Ship a working demo good enough to link from a portfolio site

## 2. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Backend framework | FastAPI | async, Pydantic-native |
| Agent orchestration | LangGraph | StateGraph, not a single prompt |
| LLM | Claude API | vision for screenshots/scanned PDFs, tool-use for structured output |
| PDF/DOCX parsing | PyMuPDF/pdfplumber, python-docx | fallback to Claude vision for scanned PDFs |
| Database | PostgreSQL + SQLAlchemy | SQLite acceptable for local dev/demo |
| Frontend | React | built after backend is functional |
| Deployment | Docker → Render/Railway (backend), Vercel (frontend) | |

## 3. Data model

**ProjectSpecState** (shared state object passed through the LangGraph, and the shape of
the API response):

```python
class Risk(BaseModel):
    description: str
    severity: Literal["low", "medium", "high"]

class ProjectSpecState(BaseModel):
    project_name: str
    client_goals: list[str]
    features: list[str]
    unknown_requirements: list[str]
    risks: list[Risk]
    complexity_score: float  # 0-10
    follow_up_questions: list[str]
```

**Database tables**

- `projects` — id, name, created_at, status
- `input_files` — project_id, source_type, storage_path, extracted_text
- `spec_versions` — project_id, version_number, state_json, created_at
  (keeps history every time a follow-up answer updates the spec)

## 4. Agent pipeline (LangGraph)

Each node takes the running state, does one focused job, and returns an updated state.
Every node's LLM call uses forced tool-use against a Pydantic schema — never free-text JSON.

1. **Normalize** — merge all input files into one clean text+image bundle, tag source type
2. **Extract** — pull raw goals, features, and requirement statements from the normalized input
3. **Classify** — sort extracted items into `client_goals`, `features`, `unknown_requirements`
4. **Assess risk** — flag ambiguous/missing/contradictory requirements, assign severity
5. **Score complexity** — combine feature count + risk severity into a 0–10 score
6. **Generate questions** — turn every `unknown_requirement` into a concrete follow-up question
7. **Compile spec** — assemble final `ProjectSpecState`, persist as a new `spec_versions` row

Feedback loop: `POST /projects/{id}/answer` re-enters the graph at **Extract** with the new
answer appended to context, rather than starting over.

## 5. API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/projects` | Upload file(s)/pasted text → run full pipeline → return spec |
| GET | `/projects/{id}` | Fetch current spec + version history |
| POST | `/projects/{id}/answer` | Submit answer to a follow-up question → updated spec |
| GET | `/projects/{id}/export` | Export spec as PDF/Markdown |

## 6. Backend folder structure

```
backend/
  app/
    main.py
    api/
      routes_upload.py
      routes_projects.py
    preprocessing/
      pdf_parser.py
      docx_parser.py
      vision_extractor.py
      normalizer.py
    agents/
      graph.py
      state.py
      nodes/
        extract.py
        classify.py
        risk.py
        complexity.py
        questions.py
    db/
      models.py
      session.py
    core/
      config.py
      claude_client.py
  requirements.txt
  Dockerfile
```

## 7. Build phases

Use each phase as a separate Claude Code `/plan` or `/goals` target — don't ask it to build
everything in one pass.

- **Phase 1 — Skeleton**: FastAPI app boots, health check route, project structure scaffolded, `.env` config loaded
- **Phase 2 — Preprocessing**: parsers for PDF/DOCX/pasted text working standalone (test with sample files before touching agents)
- **Phase 3 — Agent pipeline**: LangGraph `graph.py` with all 7 nodes wired, structured output validated against the Pydantic schema, tested against one sample transcript end-to-end
- **Phase 4 — Persistence**: DB models, save/load spec versions, wire `/projects` and `/projects/{id}`
- **Phase 5 — Feedback loop**: `/projects/{id}/answer` re-enters the graph correctly, new version saved
- **Phase 6 — Frontend**: React upload UI, spec display matching the target output format, follow-up Q&A UI
- **Phase 7 — Polish**: export endpoint, error handling, Docker, deploy, demo data/seed examples for the portfolio

## 8. Environment variables

```
ANTHROPIC_API_KEY=
DATABASE_URL=
FILE_STORAGE_PATH=
```

## 9. Testing checklist

- [ ] Each parser handles a malformed/empty file without crashing
- [ ] Each agent node returns valid schema output on a deliberately messy sample input
- [ ] Full pipeline run on a real-world messy example (e.g. a rambling WhatsApp transcript)
- [ ] Follow-up answer loop actually updates `unknown_requirements` instead of duplicating them
- [ ] API returns consistent JSON shape across all endpoints
