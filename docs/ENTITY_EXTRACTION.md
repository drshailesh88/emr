# Clinical Entity Extraction - Real-Time NLP Integration

## Overview

The DocAssist EMR now features real-time clinical entity extraction that automatically identifies and highlights medical entities as you type. This AI-powered feature helps doctors by:

1. **Automatically extracting** symptoms, diagnoses, medications, vitals, and more
2. **Highlighting entities** inline with color-coded tags
3. **Generating summaries** organized by clinical category
4. **Learning from corrections** when you fix misidentified entities

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Central Panel (UI)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Clinical Notes Field                                  │  │
│  │ (Doctor types: "45F k/c DM2, HTN. C/o chest pain...") │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│            [300ms debounce timer]                            │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Loading Indicator: "Extracting entities..."          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Clinical NLP Service Layer                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ClinicalNoteExtractor.extract_entities()             │  │
│  │  ├─ MedicalNER (Named Entity Recognition)            │  │
│  │  ├─ Abbreviations expansion                          │  │
│  │  ├─ Pattern matching (vitals, durations)             │  │
│  │  └─ ICD-10 mapping                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    UI Update Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ExtractedSummaryPanel (Organized by Category)        │  │
│  │  ├─ Patient: 45F                                     │  │
│  │  ├─ Chief Complaint: chest pain x 2 days             │  │
│  │  ├─ History: Type 2 DM, Hypertension                 │  │
│  │  ├─ Vitals: BP 150/90, Pulse 88/min                  │  │
│  │  ├─ Symptoms: chest pain, breathlessness             │  │
│  │  ├─ Diagnoses: Unstable angina                       │  │
│  │  ├─ Medications: Metformin 500mg BD, Telmisartan 40mg│  │
│  │  └─ Investigations: CBC, Troponin, ECG               │  │
│  │                [Edit] buttons for corrections         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Entity Types

The system recognizes and color-codes the following entity types:

| Entity Type    | Color  | Examples                                      |
|----------------|--------|-----------------------------------------------|
| **Symptoms**   | Orange | chest pain, breathlessness, fever, dizziness  |
| **Diagnoses**  | Blue   | diabetes mellitus, hypertension, unstable angina |
| **Medications**| Green  | Metformin 500mg, Aspirin 75mg, Atorvastatin   |
| **Vitals**     | Pink   | BP 150/90, Pulse 88/min, SpO2 96%            |
| **Measurements**| Purple| weight 70kg, height 170cm, BMI 24.2           |
| **Durations**  | Gray   | x 2 days, since 3 weeks, for 1 month          |
| **Investigations**| Amber | CBC, HbA1c, ECG, chest X-ray                |
| **Procedures** | Cyan   | PCI, angioplasty, endoscopy, biopsy           |

## Supported Abbreviations (50+)

### Chief Complaint & History
- `c/o` → complaining of
- `h/o` → history of
- `k/c` → known case of
- `s/o` → suggestive of
- `s/p` → status post
- `p/w` → presented with

### Common Diagnoses
- `DM` / `DM2` → diabetes mellitus / type 2 diabetes
- `HTN` → hypertension
- `IHD` / `CAD` → ischemic heart disease / coronary artery disease
- `CVA` → cerebrovascular accident
- `CKD` → chronic kidney disease
- `COPD` → chronic obstructive pulmonary disease
- `TB` / `PTB` → tuberculosis / pulmonary tuberculosis
- `GERD` → gastroesophageal reflux disease
- `UTI` → urinary tract infection
- `ACS` → acute coronary syndrome

### Vitals & Examinations
- `BP` → blood pressure
- `PR` / `HR` → pulse rate / heart rate
- `RR` → respiratory rate
- `SpO2` → oxygen saturation
- `CVS` → cardiovascular system
- `RS` → respiratory system
- `CNS` → central nervous system
- `P/A` → per abdomen

### Medication Frequencies
- `OD` → once daily
- `BD` → twice daily
- `TDS` → thrice daily
- `QID` → four times daily
- `HS` → at bedtime
- `SOS` / `PRN` → as needed
- `stat` → immediately
- `AC` → before meals
- `PC` → after meals

### Investigations
- `CBC` → complete blood count
- `RBS` / `FBS` / `PPBS` → random/fasting/post-prandial blood sugar
- `HbA1c` → glycated hemoglobin
- `LFT` / `KFT` / `RFT` → liver/kidney/renal function test
- `ECG` / `EKG` → electrocardiogram
- `CXR` → chest X-ray
- `USG` → ultrasonography
- `ECHO` → echocardiography
- `TMT` → treadmill test

### Hinglish Support
- `bukhar` → fever
- `dard` → pain
- `khasi` / `khansi` → cough
- `saans` → breathing
- `ulti` → vomiting
- `dast` / `loose motion` → diarrhea
- `chakkar` → dizziness
- `kamzori` → weakness
- `pet dard` → abdominal pain
- `sir dard` / `sar dard` → headache
- `seene mein dard` → chest pain

## Usage Example

### Doctor Types:
```
45F k/c DM2, HTN. C/o chest pain x 2 days, radiating to left arm.
Associated with breathlessness, sweating. No h/o fever or cough.

On Metformin 500mg BD, Telmisartan 40mg OD.

O/E: BP 150/90, Pulse 88/min, SpO2 96%, Temp 98.2F
CVS: S1S2 normal, no murmur
RS: NVBS bilateral

Impression: Unstable angina, r/o ACS

Plan:
- Tab Aspirin 75mg OD
- Tab Atorvastatin 40mg HS
- CBC, Troponin I, ECG, ECHO
- Advice: Low salt diet, avoid exertion
- F/u after 1 week
```

### System Extracts:
```
┌─────────────────────────────────────────────────────────┐
│ ✨ AI Extracted Summary                      [✓ Accept] │
├─────────────────────────────────────────────────────────┤
│ 👤 Patient                                               │
│    Age: 45y  Gender: F                                  │
│                                                          │
│ 💬 Chief Complaint                                       │
│    45F k/c DM2, HTN                              [Edit]  │
│                                                          │
│ 📋 History                                               │
│    Type 2 diabetes mellitus                      [Edit]  │
│    Hypertension                                  [Edit]  │
│                                                          │
│ ❤️  Vitals                                                │
│    BP: 150/90 mmHg                               [Edit]  │
│    Pulse: 88 /min                                [Edit]  │
│    Temp: 36.8°C                                  [Edit]  │
│    SpO2: 96%                                     [Edit]  │
│                                                          │
│ ⚠️  Symptoms                                              │
│    chest pain                                    [Edit]  │
│    breathlessness                                [Edit]  │
│    sweating                                      [Edit]  │
│                                                          │
│ 🏥 Diagnoses                                             │
│    Unstable angina                               [Edit]  │
│                                                          │
│ 💊 Current Medications                                   │
│    Metformin 500mg BD                            [Edit]  │
│    Telmisartan 40mg OD                           [Edit]  │
│                                                          │
│ 🔬 Investigations                                        │
│    CBC                                           [Edit]  │
│    Troponin I                                    [Edit]  │
│    ECG                                           [Edit]  │
│    ECHO                                          [Edit]  │
└─────────────────────────────────────────────────────────┘
```

## Correcting Extractions

If the system misidentifies an entity:

1. **Click the [Edit] button** next to the entity
2. **Type the correct value** in the inline edit field
3. **Press Enter** to save the correction

The system logs corrections to improve future extractions.

## Performance

- **Debounce delay**: 300ms (extraction starts 300ms after you stop typing)
- **Extraction time**: ~100-500ms depending on note length
- **Runs in background**: Never blocks the UI
- **Thread-safe**: Uses proper threading for async extraction

## Implementation Files

| File | Purpose |
|------|---------|
| `/src/services/clinical_nlp/abbreviations.py` | 50+ medical abbreviations mapping |
| `/src/services/clinical_nlp/note_extractor.py` | Main extraction engine with `extract_entities()` |
| `/src/services/clinical_nlp/medical_entity_recognition.py` | NER for symptoms, diagnoses, drugs, etc. |
| `/src/ui/components/entity_highlight.py` | Inline highlighting widget (color-coded) |
| `/src/ui/components/extracted_summary.py` | Summary panel with edit capability |
| `/src/ui/central_panel.py` | Integration into main UI |

## Testing

Run the test suite:

```bash
python test_entity_extraction.py
```

Expected output:
```
======================================================================
CLINICAL ENTITY EXTRACTION INTEGRATION TESTS
======================================================================

Abbreviations             ✓ PASSED
Entity Extraction         ✓ PASSED
UI Components             ✓ PASSED
Integration               ✓ PASSED

Total: 4/4 tests passed

🎉 All tests passed! Entity extraction is working correctly.
```

## Future Enhancements

### Planned Features
1. **LLM-enhanced extraction**: Use Ollama for complex entity disambiguation
2. **Custom entity types**: Allow doctors to define clinic-specific entities
3. **ML feedback loop**: Train on corrections to improve accuracy
4. **Multi-language support**: Expand Hinglish vocabulary
5. **Voice input integration**: Extract entities from voice transcription
6. **Export extracted data**: Pre-fill prescription form from extracted entities
7. **Historical learning**: Learn from doctor's past notes to personalize extraction

### Privacy & Security
- **Local-only processing**: All extraction happens on device, no cloud
- **No network calls**: Extraction works completely offline
- **Data privacy**: Patient data never leaves the device
- **HIPAA-ready**: Designed for compliance with medical data regulations

## Troubleshooting

### Extraction not appearing
- Ensure notes are at least 20 characters
- Check for JavaScript console errors
- Verify `ClinicalNoteExtractor` is initialized

### Incorrect extractions
- Click [Edit] to correct the entity
- Report persistent issues for model improvement
- Check if abbreviation is in `abbreviations.py`

### Slow performance
- Extraction runs in background thread (shouldn't affect UI)
- For very long notes (>5000 chars), consider splitting
- Disable extraction temporarily by commenting out `on_change` handler

## API Reference

### `ClinicalNoteExtractor.extract_entities(text: str) -> dict`

Extracts all entities from clinical notes.

**Args:**
- `text` (str): Clinical notes text

**Returns:**
```python
{
    'entities': [  # List of entity spans for highlighting
        {
            'start': int,
            'end': int,
            'text': str,
            'entity_type': str,  # symptom, diagnosis, medication, etc.
            'normalized_value': str,
            'confidence': float
        }
    ],
    'summary': {  # Organized summary data
        'patient_info': {'Age': '45y', 'Gender': 'F'},
        'chief_complaint': ['chest pain x 2 days'],
        'history': ['DM2', 'HTN'],
        'vitals': {'BP': '150/90 mmHg', 'Pulse': '88 /min'},
        'symptoms': ['chest pain', 'breathlessness'],
        'diagnoses': ['Unstable angina'],
        'medications': [{'drug_name': 'Metformin', 'strength': '500mg', 'frequency': 'BD'}],
        'investigations': ['CBC', 'Troponin', 'ECG']
    }
}
```

### `expand_abbreviation(abbr: str, context: str = None) -> str`

Expands a medical abbreviation.

**Args:**
- `abbr` (str): The abbreviation to expand
- `context` (str, optional): Context for disambiguation

**Returns:**
- str: Expanded form or None if not found

**Example:**
```python
from src.services.clinical_nlp.abbreviations import expand_abbreviation

expand_abbreviation("c/o")  # → "complaining of"
expand_abbreviation("DM2")  # → "type 2 diabetes mellitus"
expand_abbreviation("BP")   # → "blood pressure"
```

## Credits

Developed for DocAssist EMR - Local-First AI-Powered EMR for Indian Doctors

Built with:
- Pattern-based extraction for vitals and durations
- Rule-based NER for Indian medical terminology
- ICD-10 mapping for standardized diagnoses
- Hinglish support for code-mixed clinical notes
