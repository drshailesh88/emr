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
5. **Privacy**: No network calls except to localhost:11434 (Ollama)

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
