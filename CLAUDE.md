# DocAssist EMR - Local-First AI-Powered EMR

> **⚠️ CONTEXT RESET REMINDER**: When your context resets, immediately re-read the **Development Toolkit (MANDATORY)** section below. Use Spec-Kit for planning and Ralph Wiggum for iterative development.

## Project Vision
A local-first EMR for Indian doctors that runs entirely offline with local LLM.
Core differentiator: Natural language search and RAG on patient records.

**Goal**: Change the practice of a million doctors from pen-and-paper to digital EMR by making adoption frictionless and the experience premium.

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

> **🔴 CRITICAL**: These tools are REQUIRED for all complex development. If you're about to implement a feature, refactor code, or fix bugs — STOP and use these tools first. On every context reset, re-read this section before proceeding.

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
- **Workflow**: Always run `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` before coding
- **Always check**: `.specify/ROADMAP.md` for current project state

### Ralph Wiggum (Iterative Loop Development)
- **Source**: https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum
- **Purpose**: Enables iterative, self-improving development loops
- **Commands**:
  - `/ralph-loop "<prompt>" --max-iterations <n> --completion-promise "<text>"`
  - `/cancel-ralph` — Stop an active loop
- **When to use**: TDD cycles, bug fixing loops, iterative refinement
- **Best for**: Tasks with clear completion criteria (tests pass, linter clean)
- **Example**: `/ralph-loop "fix all type errors" --max-iterations 10 --completion-promise "0 errors"`

### Decision Matrix
| Situation | Use This Tool |
|-----------|---------------|
| New feature request | Spec-Kit (`/speckit.specify`) |
| Bug that needs investigation | Spec-Kit (`/speckit.plan`) |
| Tests failing in loop | Ralph Wiggum |
| Linter errors to fix | Ralph Wiggum |
| Architecture decision | Spec-Kit (`/speckit.constitution`) |
| Refactoring existing code | Spec-Kit → Ralph Wiggum |

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

### Pricing Tiers
| Tier | Storage | Price | Features |
|------|---------|-------|----------|
| Free | 1 GB | ₹0 | Desktop app, local backup, local AI, BYOS |
| Essential | 10 GB | ₹199/mo | + Cloud backup, mobile sync, 30-day history |
| Professional | 50 GB | ₹499/mo | + Cloud AI, SMS reminders, priority support |
| Clinic | 200 GB | ₹2,499/mo | + 5 users, audit dashboard, admin controls |
| Hospital | 1 TB | ₹9,999/mo | + Unlimited users, on-premise option, SLA |

*Early adopter pricing locked for first 1,000 users. Prices may increase for new subscribers.*

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

## Mobile App Strategy (DocAssist Mobile)

### Strategic Rationale
Indian doctors need EMR access anywhere — at home, in satellite clinics, during emergencies. A mobile companion app removes the "I'm not at my desk" friction that prevents EMR adoption.

### Privacy-First Architecture Decision

**Recommended: Tiered Privacy Model**

| Tier | Name | LLM Location | Privacy Level | Target User |
|------|------|--------------|---------------|-------------|
| 1 | Mobile Lite | None | Maximum | Privacy-purists, view-only use |
| 2 | Mobile Pro | On-device (Gemma 2B) | High | Full offline capability |
| 3 | Mobile Cloud | Cloud API (opt-in) | Moderate* | Speed-focused, explicit consent |

*Cloud tier requires explicit user consent with clear privacy warnings

### Tier 1: DocAssist Mobile Lite (Recommended MVP)
- **Philosophy**: Read-heavy, write-light companion
- **Features**:
  - View patient records (synced via E2E encrypted backup)
  - Quick patient search (local SQLite, no LLM needed)
  - Add appointment / call patient shortcuts
  - View today's schedule
  - Emergency patient lookup
  - Share prescription PDF (already generated on desktop)
- **No LLM**: All AI features require desktop
- **Privacy**: Maximum — no patient data leaves device, no cloud AI
- **Best for**: Quick reference between consultations

### Tier 2: DocAssist Mobile Pro (Future)
- **On-device LLM**: Gemma 2B (~1.5GB) via llama.cpp or MLC-LLM
- **Features**:
  - Everything in Lite, plus:
  - AI-powered natural language patient search
  - Quick prescription generation (small model, simpler output)
  - Voice-to-text clinical notes
- **Trade-offs**:
  - Slower inference (2-5 seconds)
  - Battery drain during LLM use
  - Limited context window
- **Privacy**: High — all processing on-device

### Tier 3: DocAssist Mobile Cloud (Optional Add-on)
- **Cloud LLM**: API calls to privacy-respecting service
- **Explicit Consent Flow**:
  ```
  ⚠️ This feature sends anonymized patient context to our AI service.
  - Patient names are replaced with [Patient]
  - Phone numbers and addresses are removed
  - Only clinical context is sent

  Do you consent? [Yes, I understand] [No, use offline mode]
  ```
- **Best for**: Doctors who prioritize speed over maximum privacy
- **Revenue opportunity**: Premium subscription tier

### Mobile Tech Stack
```
Framework: Flet (same as desktop, compiles to iOS/Android)
Database: SQLite (local, synced from desktop backup)
Sync: E2E encrypted cloud backup (already implemented)
LLM (Tier 2): llama.cpp / MLC-LLM with Gemma 2B
Voice: Whisper.cpp (on-device) or iOS/Android native
```

### Data Sync Architecture
```
┌─────────────────┐                    ┌─────────────────┐
│  Desktop EMR    │                    │   Mobile App    │
│  (Primary)      │                    │  (Companion)    │
├─────────────────┤                    ├─────────────────┤
│ SQLite + Chroma │                    │ SQLite (subset) │
│ Full LLM        │                    │ Optional LLM    │
│ Full features   │                    │ Core features   │
└────────┬────────┘                    └────────▲────────┘
         │                                      │
         ▼                                      │
┌─────────────────────────────────────────────────────────┐
│              DocAssist Cloud (E2E Encrypted)            │
│  - Encrypted backup blobs (server cannot decrypt)       │
│  - Sync metadata (timestamps, patient count only)       │
│  - Conflict resolution via timestamp + device ID        │
└─────────────────────────────────────────────────────────┘
```

### Premium UX Principles
1. **60fps animations**: Smooth transitions, no jank
2. **Typography**: Noto Sans for Hindi support, clear hierarchy
3. **Touch targets**: 48px minimum for all interactive elements
4. **Haptic feedback**: Subtle vibration on save, delete, important actions
5. **Dark mode**: AMOLED-optimized (#000000 background)
6. **Loading states**: Skeleton screens, never blank
7. **Offline-first**: App works immediately, syncs in background
8. **India-optimized**: Works on ₹10K phones, low RAM tolerance

### Mobile Project Structure
```
docassist_mobile/
├── main.py                 # Mobile entry point
├── src/
│   ├── ui/
│   │   ├── mobile_app.py       # Main mobile app (Flet)
│   │   ├── patient_list.py     # Scrollable patient list
│   │   ├── patient_detail.py   # Patient view screen
│   │   ├── quick_actions.py    # Floating action buttons
│   │   └── sync_indicator.py   # Sync status widget
│   ├── services/
│   │   ├── sync_client.py      # Download/decrypt backups
│   │   ├── local_db.py         # Mobile SQLite operations
│   │   └── mobile_llm.py       # Optional on-device LLM
│   └── models/
│       └── schemas.py          # Shared with desktop
└── assets/
    └── icons/                  # App icons, splash screen
```

### App Store Strategy
- **iOS**: App Store via Flet's iOS build
- **Android**: Google Play Store via Flet's Android build
- **Pricing**:
  - Mobile Lite: Free (included with any subscription)
  - Mobile Pro (on-device AI): ₹299/mo add-on
  - Mobile Cloud (cloud AI): Included in Professional tier (₹499/mo)
- **Rating goal**: 4.5+ stars, respond to all reviews within 24 hours

### Development Phases
1. **Phase 1**: Mobile Lite MVP (view-only, sync from desktop)
2. **Phase 2**: Edit capabilities (add visits, investigations)
3. **Phase 3**: On-device LLM (Tier 2)
4. **Phase 4**: Cloud LLM option (Tier 3)
5. **Phase 5**: Multi-device real-time sync
