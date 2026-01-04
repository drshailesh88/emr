# DocAssist EMR - Local-First AI-Powered EMR

## Project Vision
A local-first EMR for Indian doctors that runs entirely offline with local LLM.
Core differentiator: Natural language search and RAG on patient records.

## Instruction Sync
- Any change to project instructions must be replicated across `CLAUDE.md`, `AGENTS.md`, `CODEX.md`, `GEMINI.md`, and `GROK.md`.

## Tech Stack (FIXED - DO NOT CHANGE)
- **Language**: Python 3.11+
- **GUI**: Flet (NOT Tkinter, NOT PyQt, NOT Electron)
- **Database**: SQLite for structured data
- **Vector Store**: ChromaDB (local folder storage)
- **LLM**: Ollama (auto-detects RAM, loads appropriate model)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **PDF**: fpdf2

## RAM-Based Model Selection
```python
RAM < 6GB  → qwen2.5:1.5b (uses ~1.2GB)
RAM 6-10GB → qwen2.5:3b (uses ~2.5GB)
RAM > 10GB → qwen2.5:7b (uses ~5GB)
```

## Project Structure
```
docassist/
├── main.py                 # Entry point
├── requirements.txt
├── .env
├── data/
│   ├── clinic.db          # SQLite database
│   └── chroma/            # Vector embeddings
├── src/
│   ├── __init__.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py         # Main Flet app
│   │   ├── patient_panel.py    # Left panel
│   │   ├── central_panel.py    # Center (prescription, etc.)
│   │   └── agent_panel.py      # Right panel (RAG chat)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── database.py    # SQLite operations
│   │   ├── llm.py         # Ollama integration
│   │   ├── rag.py         # ChromaDB + retrieval
│   │   └── pdf.py         # Prescription PDF
│   └── models/
│       ├── __init__.py
│       └── schemas.py     # Pydantic models
└── prompts/
    ├── prescription.txt
    └── rag_query.txt
```

## Database Schema

### patients
- id INTEGER PRIMARY KEY
- uhid TEXT UNIQUE (auto-generated)
- name TEXT NOT NULL
- age INTEGER
- gender TEXT (M/F/O)
- phone TEXT
- address TEXT
- created_at TIMESTAMP

### visits
- id INTEGER PRIMARY KEY
- patient_id INTEGER FK
- visit_date DATE
- chief_complaint TEXT
- clinical_notes TEXT
- diagnosis TEXT
- prescription_json TEXT
- created_at TIMESTAMP

### investigations
- id INTEGER PRIMARY KEY
- patient_id INTEGER FK
- test_name TEXT
- result TEXT
- unit TEXT
- reference_range TEXT
- test_date DATE
- is_abnormal BOOLEAN

### procedures
- id INTEGER PRIMARY KEY
- patient_id INTEGER FK
- procedure_name TEXT
- details TEXT
- procedure_date DATE
- notes TEXT

## RAG Strategy

### Patient Search (across all patients)
1. Each patient has an embedded "summary" combining:
   - Name, UHID, age, gender
   - Key diagnoses
   - Major procedures (PCI, CABG, etc.)
2. Natural language query searches these summaries
3. Returns matching patients with relevance score

### Current Patient RAG (within one patient)
1. All visits, investigations, procedures are embedded
2. Query searches within this patient's documents only
3. LLM generates answer from retrieved context

## UI Layout
```
┌──────────────────────────────────────────────────────────────┐
│  DocAssist EMR                              [Settings] [?]   │
├─────────────┬────────────────────────────┬───────────────────┤
│ PATIENTS    │     CENTRAL PANEL          │   AI ASSISTANT    │
│             │                            │                   │
│ [🔍 Search] │  Patient: Ram Lal (M, 65)  │ Ask about this    │
│             │  UHID: EMR-2024-0001       │ patient...        │
│ ─────────── │                            │                   │
│ • Ram Lal   │  ┌─ Tabs ──────────────┐   │ ┌───────────────┐ │
│ • Priya S   │  │[Rx][History][Labs]  │   │ │ What was his  │ │
│ • Amit K    │  └────────────────────-┘   │ │ last creati-  │ │
│             │                            │ │ nine level?   │ │
│ [+ New]     │  Chief Complaint:          │ └───────────────┘ │
│             │  [________________]        │                   │
│             │                            │ [Send]            │
│             │  Clinical Notes:           │ ─────────────────  │
│             │  ┌──────────────────┐      │                   │
│             │  │ Pt c/o chest     │      │ Last creatinine   │
│             │  │ pain x 2 days... │      │ was 1.4 mg/dL on  │
│             │  └──────────────────┘      │ 10-Dec-2024       │
│             │                            │                   │
│             │  [Generate Rx] [Save]      │                   │
└─────────────┴────────────────────────────┴───────────────────┘
```

## Critical Rules

1. **Threading**: Use threading for LLM calls, never block UI
2. **Validation**: Always validate LLM JSON output with Pydantic
3. **Draft Mode**: LLM output shown as draft, doctor must confirm
4. **Error Handling**: Graceful degradation if Ollama not running
5. **Privacy**: No network calls except to localhost:11434 (Ollama) and optional encrypted backup service

## Development Toolkit (MANDATORY)

> **CRITICAL REMINDER**: On every context reset, RE-READ THIS SECTION FIRST.
> These tools are REQUIRED for all significant development work on this project.
> DO NOT start implementing features without using spec-kit for planning.

### Spec-Kit (Specification-Driven Development)
- **Source**: https://github.com/github/spec-kit
- **Install**: `uvx specify` or `uv tool install specify`
- **Specs Location**: `.specify/specs/` — All feature specifications live here
- **Commands**:
  - `/speckit.constitution` — Establish project governance
  - `/speckit.specify` — Define requirements and user stories
  - `/speckit.plan` — Create technical implementation strategies
  - `/speckit.tasks` — Generate actionable task lists
  - `/speckit.implement` — Execute the complete build
- **When to use**: New features, major refactors, unclear requirements
- **Always check**: `.specify/ROADMAP.md` for current project state

### Ralph Wiggum (Iterative Loop Development)
- **Source**: https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum
- **Purpose**: Enables iterative, self-improving development loops
- **Commands**:
  - `/ralph-loop "<prompt>" --max-iterations <n> --completion-promise "<text>"`
  - `/cancel-ralph` — Stop an active loop
- **When to use**: TDD cycles, bug fixing loops, iterative refinement
- **Best for**: Tasks with clear completion criteria (tests pass, linter clean)

### Development Workflow
1. **Before any major feature**: Create spec in `.specify/specs/XX-feature-name/spec.md`
2. **For iterative tasks**: Use ralph-loop with clear completion promise
3. **Always test**: Run `pytest tests/` after changes
4. **Check roadmap**: Verify feature aligns with current phase

## Premium UI Philosophy (CRITICAL)

> **Goal**: Create a habit-forming product that feels like Apple, Mercedes, Nike — not generic software.

### Design Principles
1. **Quiet Luxury**: Restrained palette, generous whitespace, subtle depth
2. **Professional Authority**: Medical-grade precision, clear hierarchy
3. **Effortless Flow**: Zero cognitive friction, natural eye movement

### UI Implementation Rules
1. **NEVER use hard-coded colors** — Always use design tokens from `src/ui/tokens.py`
2. **NEVER use magic numbers** — Use spacing scale (4, 8, 12, 16, 24, 32px)
3. **Component files < 300 lines** — Extract sub-components when growing
4. **Premium animations** — Subtle hover, smooth transitions, micro-interactions
5. **Consistent typography** — Use typography scale, not arbitrary font sizes

### Current UI Spec
- See: `.specify/specs/22-premium-ui/spec.md`
- Design tokens: `src/ui/tokens.py`
- Theme system: `src/ui/themes.py`

## Cloud Backup Strategy (E2E Encrypted)

### Architecture (WhatsApp-style Zero-Knowledge)
```
Doctor's Device                    DocAssist Cloud
┌─────────────────┐               ┌─────────────────┐
│ SQLite + Chroma │               │ Encrypted Blobs │
│   (plaintext)   │               │ (cannot decrypt)│
└────────┬────────┘               └────────▲────────┘
         │                                 │
         ▼                                 │
┌─────────────────┐     AES-256-GCM       │
│ Client-Side     │────────────────────────┘
│ Encryption      │
│ (PyNaCl/Tink)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Key Protection Options                 │
│  A) 64-digit key (user writes down)     │
│  B) Password + Argon2 KDF               │
│  C) Password + HSM vault (premium)      │
└─────────────────────────────────────────┘
```

### Implementation Modules
- `src/services/backup.py` — Backup creation, encryption, chunking
- `src/services/crypto.py` — PyNaCl encryption, Argon2 key derivation
- `src/services/sync.py` — Cloud upload/download, conflict resolution

### Key Principles
1. **Zero-knowledge**: Server stores only encrypted blobs
2. **Client-side encryption**: All encryption happens on device
3. **Key never leaves device**: Password derives key locally via Argon2
4. **Optional feature**: Core app works fully offline without backup
5. **BYOS support**: Doctors can use their own S3/Backblaze/Google Drive

### Pricing Tiers (Future)
| Tier   | Storage | Price    | Features                    |
|--------|---------|----------|-----------------------------|
| Free   | 1 GB    | ₹0       | Manual backup, BYOS         |
| Basic  | 10 GB   | ₹99/mo   | Auto-backup, 30-day history |
| Pro    | 50 GB   | ₹299/mo  | + Multi-device sync         |
| Clinic | 200 GB  | ₹999/mo  | + 5 users, audit log        |

## Prescription JSON Schema
```json
{
  "diagnosis": ["Primary", "Secondary"],
  "medications": [
    {
      "drug_name": "Metformin",
      "strength": "500mg",
      "form": "tablet",
      "dose": "1",
      "frequency": "BD",
      "duration": "30 days",
      "instructions": "after meals"
    }
  ],
  "investigations": ["CBC", "HbA1c"],
  "advice": ["Diet control", "Exercise"],
  "follow_up": "2 weeks",
  "red_flags": ["Chest pain", "Breathlessness"]
}
```
