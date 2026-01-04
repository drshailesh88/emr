# DocAssist EMR - Agent Instructions

## Purpose
Local-first EMR for Indian doctors that runs entirely offline with a local LLM.
Core differentiator: natural language search and RAG on patient records.

## Instruction Sync
- Any change to project instructions must be replicated across `CLAUDE.md`, `AGENTS.md`, `CODEX.md`, `GEMINI.md`, and `GROK.md`.

## Tech Stack (fixed - do not change)
- Language: Python 3.11+
- GUI: Flet (do not switch to Tkinter, PyQt, Electron)
- Database: SQLite
- Vector store: ChromaDB (local folder storage)
- LLM runtime: Ollama (local)
- Embeddings: sentence-transformers (all-MiniLM-L6-v2)
- PDF: fpdf2

## Runtime Rules
- Local-first: no network calls except to localhost:11434 for Ollama.
- LLM calls must be threaded; never block the Flet UI thread.
- Validate LLM JSON output with Pydantic models in `src/models/schemas.py`.
- Treat LLM output as a draft; require explicit doctor confirmation before saving.
- Degrade gracefully if Ollama is not running.

## RAM-Based Model Selection
- RAM < 6GB  -> qwen2.5:1.5b
- RAM 6-10GB -> qwen2.5:3b
- RAM > 10GB -> qwen2.5:7b

## Project Structure
docassist/
- main.py
- requirements.txt
- data/
  - clinic.db
  - chroma/
- src/
  - ui/ (Flet app)
  - services/ (database, LLM, RAG, PDF)
  - models/ (Pydantic schemas)
- prompts/ (LLM prompt templates)

## Database Schema
patients
- id INTEGER PRIMARY KEY
- uhid TEXT UNIQUE (auto-generated)
- name TEXT NOT NULL
- age INTEGER
- gender TEXT (M/F/O)
- phone TEXT
- address TEXT
- created_at TIMESTAMP

visits
- id INTEGER PRIMARY KEY
- patient_id INTEGER FK
- visit_date DATE
- chief_complaint TEXT
- clinical_notes TEXT
- diagnosis TEXT
- prescription_json TEXT
- created_at TIMESTAMP

investigations
- id INTEGER PRIMARY KEY
- patient_id INTEGER FK
- test_name TEXT
- result TEXT
- unit TEXT
- reference_range TEXT
- test_date DATE
- is_abnormal BOOLEAN

procedures
- id INTEGER PRIMARY KEY
- patient_id INTEGER FK
- procedure_name TEXT
- details TEXT
- procedure_date DATE
- notes TEXT

## RAG Strategy
Patient Search (across all patients)
1) Each patient has an embedded "summary" combining name, UHID, age, gender,
   key diagnoses, and major procedures.
2) Natural language query searches these summaries.
3) Returns matching patients with relevance score.

Current Patient RAG (within one patient)
1) All visits, investigations, procedures are embedded.
2) Query searches within this patient's documents only.
3) LLM generates answer from retrieved context.

## UI Layout
Three-panel layout: left patient list/search, center clinical notes/prescription,
right AI assistant for RAG queries.

## Development Guidance
- Keep service boundaries: UI calls DatabaseService, LLMService, RAGService, PDFService.
- Keep prompt templates in `prompts/` and load via `src/services/llm.py`.
- Keep data local in `data/`; backup service is the only optional remote dependency.

## Development Toolkit (MANDATORY)

> **CRITICAL**: On every context reset, RE-READ THIS SECTION FIRST.
> These tools are REQUIRED for all significant development work.

### Spec-Kit (Specification-Driven Development)
- Source: https://github.com/github/spec-kit
- Install: `uvx specify` or `uv tool install specify`
- Specs Location: `.specify/specs/` — All feature specifications live here
- Commands: `/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`
- When to use: New features, major refactors, unclear requirements
- Always check: `.specify/ROADMAP.md` for current project state

### Ralph Wiggum (Iterative Loop Development)
- Source: https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum
- Commands: `/ralph-loop "<prompt>" --max-iterations <n> --completion-promise "<text>"`, `/cancel-ralph`
- When to use: TDD cycles, bug fixing loops, iterative refinement

## Premium UI Philosophy (CRITICAL)

Goal: Create a habit-forming product that feels like Apple/Mercedes/Nike.

### Design Principles
1. Quiet Luxury: Restrained palette, generous whitespace, subtle depth
2. Professional Authority: Medical-grade precision, clear hierarchy
3. Effortless Flow: Zero cognitive friction, natural eye movement

### UI Implementation Rules
1. NEVER use hard-coded colors — Use design tokens from `src/ui/tokens.py`
2. NEVER use magic numbers — Use spacing scale (4, 8, 12, 16, 24, 32px)
3. Component files < 300 lines — Extract sub-components when growing
4. Premium animations — Subtle hover, smooth transitions, micro-interactions
5. Consistent typography — Use typography scale, not arbitrary font sizes

Current UI Spec: `.specify/specs/22-premium-ui/spec.md`

## Cloud Backup Strategy (E2E Encrypted)

Architecture: WhatsApp-style zero-knowledge encryption
- Client-side encryption with PyNaCl (AES-256-GCM)
- Key derived from password via Argon2
- Server stores only encrypted blobs (cannot decrypt)
- Optional feature: core app works fully offline

Implementation modules:
- src/services/backup.py — Backup creation, encryption, chunking
- src/services/crypto.py — PyNaCl encryption, Argon2 key derivation
- src/services/sync.py — Cloud upload/download, conflict resolution
