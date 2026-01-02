# DocAssist EMR - Agent Instructions

## Purpose
Local-first EMR for Indian doctors that runs entirely offline with a local LLM.
Core differentiator: natural language search and RAG on patient records.

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
- Keep data local in `data/`; do not add remote dependencies or APIs.
