# DocAssist EMR - Codex Instructions

> **⚠️ CONTEXT RESET REMINDER**: When your context resets, immediately re-read the **Development Toolkit (MANDATORY)** section below. Use Spec-Kit for planning and Ralph Wiggum for iterative development.

Use this file as the primary project guide when working as Codex.
If multiple agent instruction files exist, keep them aligned.

## Purpose
Local-first EMR for Indian doctors that runs entirely offline with a local LLM.
Core differentiator: natural language search and RAG on patient records.

**Goal**: Change the practice of a million doctors from pen-and-paper to digital EMR by making adoption frictionless and the experience premium.

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

> **🔴 CRITICAL**: These tools are REQUIRED for all complex development. If you're about to implement a feature, refactor code, or fix bugs — STOP and use these tools first.

### Spec-Kit (Specification-Driven Development)
- Source: https://github.com/github/spec-kit
- Install: `uvx specify` or `uv tool install specify`
- Commands: `/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`
- When to use: New features, major refactors, unclear requirements
- Workflow: Always run `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` before coding

### Ralph Wiggum (Iterative Loop Development)
- Source: https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum
- Commands: `/ralph-loop "<prompt>" --max-iterations <n> --completion-promise "<text>"`, `/cancel-ralph`
- When to use: TDD cycles, bug fixing loops, iterative refinement
- Example: `/ralph-loop "fix all type errors" --max-iterations 10 --completion-promise "0 errors"`

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

## Mobile App Strategy (DocAssist Mobile)

### Tiered Privacy Model
| Tier | Name | LLM Location | Privacy Level |
|------|------|--------------|---------------|
| 1 | Mobile Lite | None | Maximum (view-only) |
| 2 | Mobile Pro | On-device (Gemma 2B) | High (full offline) |
| 3 | Mobile Cloud | Cloud API (opt-in) | Moderate (explicit consent) |

### MVP (Mobile Lite)
- View patient records synced via E2E encrypted backup
- Quick patient search (local SQLite)
- Add appointments, view schedule
- No LLM — all AI features require desktop
- Maximum privacy

### Tech Stack
- Framework: Flet (same as desktop, compiles to iOS/Android)
- Database: SQLite (local, synced from desktop)
- Sync: E2E encrypted cloud backup (already implemented)

### Development Phases
1. Mobile Lite MVP (view-only, sync)
2. Edit capabilities (add visits)
3. On-device LLM (Tier 2)
4. Cloud LLM option (Tier 3)

### Premium UX Principles
- 60fps animations, no jank
- Touch targets 48px minimum
- Works on ₹10K phones
- Offline-first
- AMOLED dark mode
