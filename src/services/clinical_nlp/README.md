# Clinical NLP Engine

Revolutionary natural language processing for Indian healthcare. Extract structured clinical data from natural speech, generate differential diagnoses, and flag critical red flags.

## Features

### 🎯 Core Capabilities

1. **SOAP Note Extraction** - Convert natural language transcripts into structured SOAP notes
2. **Medical Entity Recognition** - Extract symptoms, diagnoses, medications, investigations, procedures
3. **Differential Diagnosis** - Bayesian reasoning with India-specific disease prevalence
4. **Investigation Suggestions** - Protocol-based investigation recommendations
5. **Red Flag Detection** - Identify time-critical conditions requiring immediate action
6. **Clinical Summaries** - Generate concise natural language summaries

### 🇮🇳 India-Specific Features

- **Hinglish Support**: Handles code-mixed Hindi-English speech (e.g., "patient ko fever hai for 3 days")
- **Indian Medical Abbreviations**: c/o, h/o, s/o, k/c/o, etc.
- **Local Drug Brands**: Glycomet, Crocin, Ecosprin, Telma, etc.
- **Disease Prevalence**: Bayesian priors for dengue, malaria, TB, diabetes, hypertension
- **Indian Dosing**: OD, BD, TDS, QID, HS, SOS, stat

## Installation

```bash
# Core dependencies
pip install pydantic psutil requests

# Optional: For LLM-enhanced extraction
# Requires Ollama running locally
```

## Quick Start

### Extract SOAP Note

```python
from src.services.clinical_nlp import ClinicalNoteExtractor
from src.services.llm import LLMService

# Initialize
llm = LLMService()
extractor = ClinicalNoteExtractor(llm_service=llm)

# Clinical transcript (can be Hinglish)
transcript = """
Patient c/o chest pain for 2 days. BP 150/95, PR 88.
Impression: Acute coronary syndrome.
Tab. Aspirin 325mg stat, Tab. Atorvastatin 80mg OD.
Investigations: ECG stat, Troponin I.
"""

# Extract structured data
soap = extractor.extract_soap_note(transcript)

print(soap.chief_complaint)  # "chest pain"
print(soap.vitals)  # {"BP": "150/95", "Pulse": "88 bpm"}
print(soap.diagnoses)  # ["Acute coronary syndrome"]
print(soap.medications)  # [Medication(...), ...]
```

### Extract Medical Entities

```python
from src.services.clinical_nlp import MedicalNER

ner = MedicalNER()

text = "Patient has severe headache since 3 days with fever. Diagnosed with viral meningitis."

# Extract components
symptoms = ner.extract_symptoms(text)
# [Symptom(name="headache", duration="3 days", severity=Severity.SEVERE), ...]

diagnoses = ner.extract_diagnoses(text)
# [Diagnosis(name="Viral Meningitis", icd10_code=None), ...]

drugs = ner.extract_drugs(text)
investigations = ner.extract_investigations(text)
```

### Generate Differential Diagnoses

```python
from src.services.clinical_nlp import ClinicalReasoning
from src.services.clinical_nlp import Symptom, ClinicalContext

# Patient presentation
symptoms = [
    Symptom(
        name="chest pain",
        duration="4 hours",
        severity="severe",
        radiation="left arm",
        associated_symptoms=["sweating", "breathlessness"],
    )
]

# Patient context
context = ClinicalContext(
    patient_age=58,
    patient_gender="M",
    known_conditions=["Diabetes Mellitus", "Hypertension"],
)

# Generate differentials
reasoner = ClinicalReasoning()
differentials = reasoner.generate_differentials(symptoms, context)

for diff in differentials:
    print(f"{diff.diagnosis}: {diff.probability*100:.1f}%")
    print(f"  Investigations: {diff.recommended_investigations}")
    print(f"  Urgency: {diff.treatment_urgency}")
```

### Detect Red Flags

```python
presentation = {
    "symptoms": [
        Symptom(name="chest pain", severity="severe"),
    ],
    "vitals": {"BP": "160/100", "SpO2": "88%"},
    "history": "crushing chest pain radiating to jaw",
}

red_flags = reasoner.flag_red_flags(presentation)

for flag in red_flags:
    if flag.time_critical:
        print(f"🔴 {flag.category}: {flag.description}")
        print(f"   Action: {flag.action_required}")
```

## Architecture

### Components

```
clinical_nlp/
├── entities.py                     # Data classes for all entities
├── note_extractor.py               # SOAP note extraction
├── medical_entity_recognition.py   # NER for medical entities
├── clinical_reasoning.py           # Differential diagnosis, red flags
├── example_usage.py                # Comprehensive examples
└── README.md                       # This file
```

### Data Flow

```
Natural Language Transcript
         ↓
┌─────────────────────┐
│ ClinicalNoteExtractor│
└─────────────────────┘
         ↓
┌─────────────────────┐
│  Pattern Matching   │
│  + LLM Enhancement  │
└─────────────────────┘
         ↓
    Structured SOAPNote
         ↓
┌─────────────────────┐
│   MedicalNER        │
└─────────────────────┘
         ↓
  Medical Entities
         ↓
┌─────────────────────┐
│ ClinicalReasoning   │
└─────────────────────┘
         ↓
  Differentials + Investigations + Red Flags
```

## Entity Types

### Symptom
```python
@dataclass
class Symptom:
    name: str
    duration: Optional[str]          # "3 days", "2 weeks"
    severity: Optional[Severity]     # MILD, MODERATE, SEVERE, CRITICAL
    onset: Optional[Onset]           # ACUTE, SUBACUTE, CHRONIC, SUDDEN
    location: Optional[str]          # "chest", "abdomen"
    quality: Optional[str]           # "sharp", "dull", "throbbing"
    radiation: Optional[str]         # "to left arm"
    aggravating_factors: List[str]
    relieving_factors: List[str]
    associated_symptoms: List[str]
```

### Diagnosis
```python
@dataclass
class Diagnosis:
    name: str
    icd10_code: Optional[str]
    confidence: float                # 0-1 scale
    is_primary: bool
    is_differential: bool
    supporting_evidence: List[str]
```

### Drug
```python
@dataclass
class Drug:
    name: str
    generic_name: Optional[str]
    brand_name: Optional[str]
    dose: Optional[str]
    strength: Optional[str]          # "500mg"
    route: str                       # "oral", "IV", "IM"
    frequency: Optional[str]         # "OD", "BD", "TDS"
    duration: Optional[str]          # "7 days"
    instructions: Optional[str]      # "after meals"
```

### SOAPNote
```python
@dataclass
class SOAPNote:
    # Subjective
    chief_complaint: str
    history_of_present_illness: str
    associated_symptoms: List[str]
    duration: Optional[str]

    # Objective
    vitals: Dict[str, str]
    examination_findings: List[str]

    # Assessment
    diagnoses: List[str]
    differential_diagnoses: List[str]

    # Plan
    medications: List[Drug]
    investigations: List[Investigation]
    advice: List[str]
    follow_up: Optional[str]
```

### Differential
```python
@dataclass
class Differential:
    diagnosis: str
    probability: float                          # Bayesian posterior
    prior_probability: float                    # India prevalence
    supporting_features: List[str]
    against_features: List[str]
    recommended_investigations: List[str]
    red_flags: List[str]
    treatment_urgency: str                      # "stat", "urgent", "routine"
```

### RedFlag
```python
@dataclass
class RedFlag:
    category: str                               # "cardiac", "neuro", "sepsis"
    description: str
    severity: Severity
    action_required: str
    time_critical: bool
    system: Optional[str]                       # "cardiovascular", etc.
```

## Bayesian Reasoning

The Clinical Reasoning engine uses Bayesian inference for differential diagnosis:

### Formula
```
P(Disease|Symptoms) = P(Symptoms|Disease) × P(Disease) / P(Symptoms)

Where:
- P(Disease) = Prior probability (India-specific prevalence)
- P(Symptoms|Disease) = Likelihood ratio from symptom-disease map
- P(Disease|Symptoms) = Posterior probability (what we calculate)
```

### India-Specific Priors

| Disease | Prevalence |
|---------|------------|
| Diabetes Mellitus | 8% |
| Hypertension | 25% |
| Tuberculosis | 0.2% |
| Dengue | 0.1% (seasonal) |
| Ischemic Heart Disease | 6% |
| Viral Fever | 5% |

### Likelihood Ratios

Example: Chest Pain

| Diagnosis | Likelihood Ratio |
|-----------|------------------|
| Acute Coronary Syndrome | 10.0 |
| Angina | 8.0 |
| GERD | 3.0 |
| Costochondritis | 2.0 |

## Red Flag Categories

### Cardiac
- Crushing chest pain
- Radiating to jaw/arm
- Chest pain with sweating
- Syncope with chest pain

**Action**: Emergency ECG, Troponin, immediate cardiology referral

### Neurological
- Sudden severe headache
- Worst headache of life
- Weakness one side
- Facial deviation
- Slurred speech

**Action**: Emergency CT brain, immediate neurology referral

### Sepsis
- Fever with altered sensorium
- Hypotension with fever
- Rigors

**Action**: Blood culture, broad spectrum antibiotics, ICU referral

### Respiratory
- Breathlessness at rest
- SpO2 < 90%
- Cyanosis

**Action**: Oxygen therapy, ABG, chest X-ray

## Pattern Matching

### Vital Signs Extraction

```python
VITAL_PATTERNS = {
    "bp": r"(?:BP|blood pressure)\s*[:-]?\s*(\d{2,3})/(\d{2,3})",
    "pulse": r"(?:PR|pulse|HR)\s*[:-]?\s*(\d{2,3})",
    "temp": r"(?:temp|temperature)\s*[:-]?\s*([\d.]+)\s*(?:°F|F)?",
    "spo2": r"(?:SpO2|oxygen)\s*[:-]?\s*(\d{2,3})\s*%?",
}
```

### Hinglish Translation

```python
HINGLISH_TERMS = {
    "bukhar": "fever",
    "dard": "pain",
    "khasi": "cough",
    "ulti": "vomiting",
    "chakkar": "dizziness",
    "seene mein dard": "chest pain",
}
```

### Abbreviation Expansion

```python
ABBREVIATIONS = {
    "c/o": "complains of",
    "h/o": "history of",
    "k/c/o": "known case of",
    "BP": "blood pressure",
    "OD": "once daily",
    "BD": "twice daily",
}
```

## LLM Integration

The engine supports optional LLM enhancement for complex cases:

```python
# Initialize with LLM service
llm = LLMService()
extractor = ClinicalNoteExtractor(llm_service=llm)

# LLM is used when:
# 1. Pattern matching fails to extract medications
# 2. Complex SOAP note structure
# 3. Ambiguous clinical context
```

## Performance

- **Pattern Matching**: < 10ms for typical clinical note
- **With LLM**: 1-5 seconds (depends on model size)
- **Memory**: Lightweight, < 50MB without LLM

## Indian Drug Database

Supports 100+ common Indian brands:

### Diabetes
- Glycomet, Obimet (Metformin)
- Amaryl, Glemer (Glimepiride)
- Mixtard, Lantus (Insulin)

### Hypertension
- Amlong, Stamlo (Amlodipine)
- Telma, Telsar (Telmisartan)
- Aten (Atenolol)

### Cardiac
- Ecosprin, Loprin (Aspirin)
- Atorva, Storvas (Atorvastatin)
- Clopivas (Clopidogrel)

### Common Medications
- Crocin, Dolo (Paracetamol)
- Mox, Novamox (Amoxicillin)
- Pan, Pantocid (Pantoprazole)

## Investigation Protocols

### Chest Pain Protocol
1. ECG (stat)
2. Troponin I
3. CK-MB
4. Chest X-ray
5. 2D Echo

### Fever Protocol
1. CBC with differential
2. Malaria card test
3. Dengue NS1 antigen
4. Typhoid IgM
5. Blood culture
6. Urine routine
7. Chest X-ray

### Diabetes Screening
1. Fasting blood sugar
2. HbA1c
3. Lipid profile
4. Creatinine
5. Urine microalbumin
6. Fundoscopy

## Error Handling

The engine gracefully degrades when:

- LLM service unavailable → Falls back to pattern matching
- Ambiguous input → Returns partial results with confidence scores
- Unknown drug names → Stores as-is without generic mapping
- Missing vitals → Continues with available data

## Best Practices

1. **Always provide patient context** for better differential diagnosis
2. **Use LLM service** for complex Hinglish transcripts
3. **Review red flags immediately** - they indicate time-critical conditions
4. **Validate medication extraction** - Indian drug names can be ambiguous
5. **Adjust investigation protocols** based on local availability

## Future Enhancements

- [ ] Voice-to-text integration (Whisper.cpp)
- [ ] Real-time streaming extraction
- [ ] Multi-modal (images, lab PDFs)
- [ ] Continuous learning from doctor corrections
- [ ] Regional language support (Tamil, Telugu, Bengali)
- [ ] Expanded ICD-10 mapping
- [ ] Drug-drug interaction checking
- [ ] Allergy checking

## Contributing

Contributions welcome! Priority areas:

1. More Indian drug brands
2. Regional medical terminology
3. Specialty-specific templates (cardiology, nephrology)
4. Improved ICD-10 mapping
5. Better Hinglish NLP

## License

Part of DocAssist EMR - Local-First AI-Powered EMR for Indian Doctors

## Support

For issues, questions, or suggestions:
- GitHub Issues: [Link to repo]
- Email: support@docassist.ai
- Slack: #clinical-nlp

---

**Built with ❤️ for Indian Healthcare**
