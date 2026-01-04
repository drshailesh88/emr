# Clinical NLP Engine - Quick Start Guide

Get started with the Clinical NLP Engine in 5 minutes.

## Installation

```bash
# Already included in DocAssist EMR
# No additional installation needed
```

## Basic Usage

### 1. Extract SOAP Note (Most Common Use Case)

```python
from src.services.llm import LLMService
from src.services.clinical_nlp import ClinicalNoteExtractor

# Initialize
llm = LLMService()
extractor = ClinicalNoteExtractor(llm_service=llm)

# Your clinical notes (can be Hinglish)
notes = """
Patient c/o chest pain for 2 days.
BP 150/95, PR 88.
Impression: Acute coronary syndrome.
"""

# Extract structured data
soap = extractor.extract_soap_note(notes)

# Use the data
print(soap.chief_complaint)  # "chest pain"
print(soap.vitals)           # {"BP": "150/95", "Pulse": "88 bpm"}
print(soap.diagnoses)        # ["Acute coronary syndrome"]
```

### 2. Extract Just Vitals

```python
from src.services.clinical_nlp import ClinicalNoteExtractor

extractor = ClinicalNoteExtractor()

text = "BP 120/80, PR 72, temp 98.6F, SpO2 98%"
vitals = extractor.extract_vitals(text)

print(f"BP: {vitals.bp_systolic}/{vitals.bp_diastolic}")
print(f"Pulse: {vitals.pulse}")
print(f"SpO2: {vitals.spo2}%")
```

### 3. Extract Medications

```python
from src.services.clinical_nlp import ClinicalNoteExtractor

extractor = ClinicalNoteExtractor()

text = "Tab. Paracetamol 650mg TDS for 5 days"
medications = extractor.extract_medications(text)

for med in medications:
    print(f"{med.drug_name} {med.strength} {med.frequency}")
```

### 4. Get Differential Diagnoses

```python
from src.services.clinical_nlp import ClinicalReasoning, Symptom, ClinicalContext

# Patient symptoms
symptoms = [
    Symptom(
        name="chest pain",
        duration="4 hours",
        severity="severe",
        radiation="left arm",
    )
]

# Patient context (optional but recommended)
context = ClinicalContext(
    patient_age=58,
    patient_gender="M",
    known_conditions=["Diabetes Mellitus", "Hypertension"],
)

# Generate differentials
reasoner = ClinicalReasoning()
differentials = reasoner.generate_differentials(symptoms, context)

# Top 3 differentials
for diff in differentials[:3]:
    print(f"{diff.diagnosis}: {diff.probability*100:.1f}%")
    print(f"  Recommended: {', '.join(diff.recommended_investigations[:3])}")
```

### 5. Check for Red Flags

```python
from src.services.clinical_nlp import ClinicalReasoning, Symptom

reasoner = ClinicalReasoning()

presentation = {
    "symptoms": [
        Symptom(name="chest pain radiating to jaw", severity="severe")
    ],
    "vitals": {"BP": "160/100", "SpO2": "88%"},
    "history": "crushing chest pain with sweating",
}

red_flags = reasoner.flag_red_flags(presentation)

for flag in red_flags:
    if flag.time_critical:
        print(f"🔴 {flag.category}: {flag.description}")
        print(f"   Action: {flag.action_required}")
```

## Common Patterns

### Pattern 1: EMR Visit Creation

```python
# Doctor enters clinical notes
clinical_notes = """..."""

# Extract structured data
soap = extractor.extract_soap_note(clinical_notes)

# Create visit record
visit = Visit(
    patient_id=patient.id,
    chief_complaint=soap.chief_complaint,
    clinical_notes=clinical_notes,
    diagnosis=", ".join(soap.diagnoses),
)
```

### Pattern 2: Prescription Generation

```python
# Extract SOAP note
soap = extractor.extract_soap_note(clinical_notes)

# Convert to Prescription schema
from src.models.schemas import Medication, Prescription

prescription = Prescription(
    diagnosis=soap.diagnoses,
    medications=[
        Medication(
            drug_name=drug.name,
            strength=drug.strength,
            frequency=drug.frequency,
            duration=drug.duration,
        )
        for drug in soap.medications
    ],
    investigations=[inv.name for inv in soap.investigations],
    advice=soap.advice,
    follow_up=soap.follow_up,
)
```

### Pattern 3: Clinical Decision Support

```python
# Extract symptoms
ner = MedicalNER()
symptoms = ner.extract_symptoms(clinical_notes)

# Generate differentials
reasoner = ClinicalReasoning()
differentials = reasoner.generate_differentials(symptoms, patient_context)

# Check for red flags
red_flags = reasoner.flag_red_flags({
    "symptoms": symptoms,
    "vitals": soap.vitals,
    "history": clinical_notes,
})

# Suggest investigations
investigations = reasoner.suggest_investigations(differentials)

# Present to doctor
if red_flags:
    print("⚠️ IMMEDIATE ATTENTION REQUIRED")
    for flag in red_flags:
        print(f"   {flag.description}")
```

## Hinglish Support

The engine automatically handles code-mixed Hindi-English:

```python
notes = """
Patient ko bukhar hai for 3 days with khasi.
BP 120/80 hai, temp 101F.
Dard pet mein bhi hai.
"""

soap = extractor.extract_soap_note(notes)
# Automatically translates:
# - bukhar → fever
# - khasi → cough
# - dard pet mein → abdominal pain
```

## Tips & Best Practices

### ✅ DO

- **Provide patient context** when generating differentials for better accuracy
- **Check red flags** on every critical presentation
- **Use LLM service** for complex Hinglish notes
- **Validate extracted medications** before prescribing

### ❌ DON'T

- Don't rely solely on NLP for critical decisions - always review
- Don't skip red flag checking for chest pain, breathlessness, syncope
- Don't ignore confidence scores - low confidence means review needed
- Don't use without LLM service for complex medical terminology

## Performance Notes

| Operation | Time (without LLM) | Time (with LLM) |
|-----------|-------------------|-----------------|
| Extract vitals | <10ms | N/A |
| Extract SOAP | <50ms | 1-5s |
| Generate differentials | <20ms | <50ms |
| Check red flags | <10ms | <10ms |

## Troubleshooting

### Medication extraction failing
```python
# Solution: Use LLM service
llm = LLMService()
extractor = ClinicalNoteExtractor(llm_service=llm)
```

### Hinglish not working
```python
# Check normalization
text = "Patient ko bukhar hai"
normalized = extractor._normalize_text(text)
print(normalized)  # Should contain "fever"
```

### Low differential confidence
```python
# Provide more patient context
context = ClinicalContext(
    patient_age=60,
    known_conditions=["Diabetes", "Hypertension"],
    current_medications=["Metformin", "Amlodipine"],
)
differentials = reasoner.generate_differentials(symptoms, context)
```

## Next Steps

- Read [README.md](README.md) for comprehensive documentation
- Check [example_usage.py](example_usage.py) for detailed examples
- See [integration_example.py](integration_example.py) for EMR integration
- Run tests: `pytest src/services/clinical_nlp/test_clinical_nlp.py -v`

## Support

Questions? Check:
1. [README.md](README.md) - Full documentation
2. [example_usage.py](example_usage.py) - Working examples
3. [test_clinical_nlp.py](test_clinical_nlp.py) - Test cases

---

**Get started in 3 lines:**
```python
from src.services.clinical_nlp import ClinicalNoteExtractor
extractor = ClinicalNoteExtractor()
soap = extractor.extract_soap_note("Patient c/o fever for 3 days. BP 120/80.")
```
