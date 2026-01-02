# DocAssist EMR

Local-first EMR for Indian doctors that runs fully offline with a local LLM.
Core differentiator: natural language search and RAG on patient records.

## Requirements
- Python 3.11+
- Ollama installed and running locally (http://localhost:11434)

## Setup
1) Create and activate a virtual environment.
   - macOS/Linux: `python -m venv .venv && source .venv/bin/activate`
   - Windows: `python -m venv .venv && .venv\Scripts\activate`
2) Install dependencies: `pip install -r requirements.txt`
3) Optional config: `cp .env.example .env` and edit as needed.
4) Start Ollama: `ollama serve`
5) Pull a model (pick one based on RAM):
   - < 6GB RAM: `ollama pull qwen2.5:1.5b`
   - 6-10GB RAM: `ollama pull qwen2.5:3b`
   - > 10GB RAM: `ollama pull qwen2.5:7b`
6) Run the app: `python main.py`

If Ollama is not running, the app will still start but AI features are disabled.

## Environment variables
Set these in `.env` if you want to override defaults:
- `OLLAMA_BASE_URL` (default: `http://localhost:11434`)
- `DOCASSIST_DB_PATH` (default: `data/clinic.db`)
- `DOCASSIST_CHROMA_DIR` (default: `data/chroma`)
- `DOCASSIST_PDF_DIR` (default: `data/prescriptions`)

## Data
Local data is stored in `data/` (SQLite DB, Chroma vectors, PDFs). This folder is ignored by git.

## Notes
- The app uses a 3-panel Flet UI (patients, clinical notes, AI assistant).
- LLM output is treated as a draft and must be confirmed before saving.
