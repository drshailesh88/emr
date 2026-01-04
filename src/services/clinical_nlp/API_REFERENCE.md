# Clinical NLP Engine - API Reference

Complete API documentation for all classes and methods.

## Table of Contents

- [ClinicalNoteExtractor](#clinicalnoteextractor)
- [MedicalNER](#medicalner)
- [ClinicalReasoning](#clinicalreasoning)
- [Entity Classes](#entity-classes)
- [Enums](#enums)

---

## ClinicalNoteExtractor

Extract structured SOAP notes from natural language transcripts.

### Constructor

```python
ClinicalNoteExtractor(llm_service=None)
```

**Parameters:**
- `llm_service` (LLMService, optional): Ollama LLM service for enhanced extraction

**Example:**
```python
from src.services.llm import LLMService
from src.services.clinical_nlp import ClinicalNoteExtractor

llm = LLMService()
extractor = ClinicalNoteExtractor(llm_service=llm)
```

### Methods

#### extract_soap_note()

```python
extract_soap_note(transcript: str) -> SOAPNote
```

Extract complete structured SOAP note from clinical transcript.

**Parameters:**
- `transcript` (str): Raw clinical notes (can be Hindi/English/Hinglish)

**Returns:**
- `SOAPNote`: Structured SOAP note with all components

**Example:**
```python
soap = extractor.extract_soap_note("""
    Patient c/o chest pain for 2 days.
    BP 150/95, PR 88.
    Impression: ACS.
""")

print(soap.chief_complaint)  # "chest pain"
print(soap.vitals)           # {"BP": "150/95", "Pulse": "88 bpm"}
```

---

#### extract_vitals()

```python
extract_vitals(transcript: str) -> Vitals
```

Extract vital signs from text into Vitals schema.

**Parameters:**
- `transcript` (str): Text containing vital signs

**Returns:**
- `Vitals`: Vitals object with extracted measurements

**Supported Patterns:**
- BP: "BP 120/80", "blood pressure 140/90"
- Pulse: "PR 72", "pulse 88", "HR 90"
- Temperature: "temp 98.6F", "temperature 37C"
- SpO2: "SpO2 98%", "oxygen 95%"
- Weight: "wt 70kg", "weight 65kgs"
- Height: "ht 170cm", "height 5.8ft"

**Example:**
```python
vitals = extractor.extract_vitals("BP 120/80, PR 72, temp 98.6F, SpO2 98%")

print(f"BP: {vitals.bp_systolic}/{vitals.bp_diastolic}")  # 120/80
print(f"Pulse: {vitals.pulse}")                           # 72
print(f"BMI: {vitals.bmi}")                               # Calculated if height/weight present
```

---

#### extract_medications()

```python
extract_medications(transcript: str) -> List[Medication]
```

Extract medications with dosing information.

**Parameters:**
- `transcript` (str): Text containing medication information

**Returns:**
- `List[Medication]`: List of extracted medications

**Supported Patterns:**
- "Tab. Paracetamol 650mg TDS"
- "Inj. Insulin 10 units SC BD"
- "Syrup Crocin 5ml TDS for 5 days"

**Example:**
```python
medications = extractor.extract_medications("""
    Tab. Crocin 650mg TDS for fever
    Tab. Glycomet 500mg BD before meals
""")

for med in medications:
    print(f"{med.drug_name} {med.strength} {med.frequency}")
```

---

## MedicalNER

Medical Named Entity Recognition for Indian clinical context.

### Constructor

```python
MedicalNER(llm_service=None)
```

**Parameters:**
- `llm_service` (LLMService, optional): Ollama LLM service for enhanced NER

---

### Methods

#### extract_symptoms()

```python
extract_symptoms(text: str) -> List[Symptom]
```

Extract symptoms with duration, severity, and onset.

**Parameters:**
- `text` (str): Clinical text to analyze

**Returns:**
- `List[Symptom]`: List of extracted symptoms

**Example:**
```python
ner = MedicalNER()
symptoms = ner.extract_symptoms("Patient has severe headache since 3 days with fever")

for symptom in symptoms:
    print(f"{symptom.name}: {symptom.duration}, {symptom.severity}")
# Output:
# headache: 3 days, Severity.SEVERE
# fever: None, None
```

---

#### extract_diagnoses()

```python
extract_diagnoses(text: str) -> List[Diagnosis]
```

Extract diagnoses with ICD-10 mapping when available.

**Parameters:**
- `text` (str): Clinical text to analyze

**Returns:**
- `List[Diagnosis]`: List of extracted diagnoses

**Supported ICD-10 Codes:** 40+ common Indian diagnoses including:
- Diabetes Mellitus (E11.9)
- Hypertension (I10)
- Tuberculosis (A15.9)
- Dengue (A90)
- Stroke (I64)

**Example:**
```python
diagnoses = ner.extract_diagnoses("Diagnosed with diabetes mellitus and hypertension")

for diag in diagnoses:
    print(f"{diag.name} ({diag.icd10_code})")
# Output:
# Diabetes Mellitus (E11.9)
# Hypertension (I10)
```

---

#### extract_drugs()

```python
extract_drugs(text: str) -> List[Drug]
```

Extract medications with name, dose, route, frequency.

**Parameters:**
- `text` (str): Clinical text to analyze

**Returns:**
- `List[Drug]`: List of extracted drugs

**Supported Indian Brands:** 100+ including:
- Glycomet, Obimet (Metformin)
- Crocin, Dolo (Paracetamol)
- Ecosprin, Loprin (Aspirin)

**Example:**
```python
drugs = ner.extract_drugs("Tab. Crocin 650mg TDS, Inj. Actrapid 10 units SC")

for drug in drugs:
    print(f"{drug.name} ({drug.generic_name}): {drug.dose} {drug.frequency}")
```

---

#### extract_investigations()

```python
extract_investigations(text: str) -> List[Investigation]
```

Extract lab tests and imaging investigations.

**Parameters:**
- `text` (str): Clinical text to analyze

**Returns:**
- `List[Investigation]`: List of extracted investigations

**Categories:**
- Lab: CBC, creatinine, HbA1c, LFT, KFT, etc.
- Imaging: X-ray, CT, MRI, ultrasound, echo
- Procedure: ECG, TMT, endoscopy, biopsy

**Example:**
```python
invs = ner.extract_investigations("Investigations: CBC, creatinine, chest X-ray, ECG")

for inv in invs:
    print(f"{inv.name} [{inv.test_type}]")
# Output:
# CBC [lab]
# Creatinine [lab]
# Chest X-ray [imaging]
# ECG [procedure]
```

---

#### extract_procedures()

```python
extract_procedures(text: str) -> List[Procedure]
```

Extract medical procedures.

**Parameters:**
- `text` (str): Clinical text to analyze

**Returns:**
- `List[Procedure]`: List of extracted procedures

**Supported Procedures:**
- PCI, PTCA, CABG
- Pacemaker, stenting
- Dialysis
- Endoscopy, colonoscopy

---

## ClinicalReasoning

Clinical reasoning engine with Bayesian inference.

### Constructor

```python
ClinicalReasoning(llm_service=None)
```

**Parameters:**
- `llm_service` (LLMService, optional): Ollama LLM service for enhanced reasoning

---

### Methods

#### generate_differentials()

```python
generate_differentials(
    symptoms: List[Symptom],
    patient_context: Optional[ClinicalContext] = None
) -> List[Differential]
```

Generate ranked differential diagnoses using Bayesian reasoning.

**Parameters:**
- `symptoms` (List[Symptom]): Patient's symptoms
- `patient_context` (ClinicalContext, optional): Patient age, comorbidities, etc.

**Returns:**
- `List[Differential]`: Ranked list of differential diagnoses

**Algorithm:**
1. Extract candidate diagnoses from symptom-disease mapping
2. Calculate Bayesian posterior: P(Disease|Symptoms) = P(Symptoms|Disease) × P(Disease) / P(Symptoms)
3. Use India-specific prevalence as priors
4. Adjust for patient context (age, comorbidities)
5. Rank by probability

**Example:**
```python
from src.services.clinical_nlp import Symptom, ClinicalContext, ClinicalReasoning

symptoms = [
    Symptom(
        name="chest pain",
        duration="4 hours",
        severity=Severity.SEVERE,
        radiation="left arm",
    )
]

context = ClinicalContext(
    patient_age=58,
    patient_gender="M",
    known_conditions=["Diabetes Mellitus", "Hypertension"],
)

reasoner = ClinicalReasoning()
differentials = reasoner.generate_differentials(symptoms, context)

for diff in differentials[:5]:
    print(f"{diff.diagnosis}: {diff.probability*100:.1f}%")
    print(f"  Prior: {diff.prior_probability*100:.2f}%")
    print(f"  Urgency: {diff.treatment_urgency}")
```

---

#### suggest_investigations()

```python
suggest_investigations(differentials: List[Differential]) -> List[Investigation]
```

Suggest investigations to rule in/out differential diagnoses.

**Parameters:**
- `differentials` (List[Differential]): List of differential diagnoses

**Returns:**
- `List[Investigation]`: Prioritized investigations

**Investigation Protocols:**
- Chest pain → ECG, Troponin, CK-MB, Echo
- Fever → CBC, malaria, dengue, typhoid, blood culture
- Breathlessness → SpO2, CXR, ECG, Echo, BNP

**Example:**
```python
investigations = reasoner.suggest_investigations(differentials)

for inv in investigations:
    print(f"{inv.name} [{inv.urgency}] - {inv.reason}")
# Output:
# ECG [urgent] - R/O Acute Coronary Syndrome
# Troponin I [urgent] - R/O Acute Coronary Syndrome
```

---

#### flag_red_flags()

```python
flag_red_flags(presentation: Dict) -> List[RedFlag]
```

Identify time-critical red flags requiring immediate attention.

**Parameters:**
- `presentation` (Dict): Clinical presentation with keys:
  - `symptoms` (List[Symptom])
  - `vitals` (Dict[str, str])
  - `history` (str)

**Returns:**
- `List[RedFlag]`: Identified red flags

**Red Flag Categories:**
- Cardiac: Crushing chest pain, radiation to jaw/arm
- Neuro: Sudden severe headache, weakness one side
- Sepsis: Fever with altered sensorium, hypotension
- Respiratory: Breathlessness at rest, SpO2 < 90%
- Hemorrhage: Hematemesis, melena, hemoptysis

**Example:**
```python
presentation = {
    "symptoms": [
        Symptom(name="chest pain radiating to jaw", severity=Severity.SEVERE)
    ],
    "vitals": {"BP": "160/100", "SpO2": "88%"},
    "history": "crushing chest pain with sweating",
}

red_flags = reasoner.flag_red_flags(presentation)

for flag in red_flags:
    if flag.time_critical:
        print(f"🔴 {flag.category.upper()}: {flag.description}")
        print(f"   Action: {flag.action_required}")
```

---

#### generate_clinical_summary()

```python
generate_clinical_summary(soap: SOAPNote) -> str
```

Generate concise natural language clinical summary.

**Parameters:**
- `soap` (SOAPNote): Structured SOAP note

**Returns:**
- `str`: Natural language summary (2-3 sentences)

**Example:**
```python
summary = reasoner.generate_clinical_summary(soap)
print(summary)
# Output:
# "Patient presents with chest pain for 2 days. Vitals: BP: 150/95, Pulse: 88 bpm.
#  Impression: Acute Coronary Syndrome. Plan: 3 medications prescribed; Investigations:
#  ECG, Troponin I; Follow-up: Emergency department referral."
```

---

## Entity Classes

### Symptom

```python
@dataclass
class Symptom:
    name: str
    duration: Optional[str] = None
    severity: Optional[Severity] = None
    onset: Optional[Onset] = None
    location: Optional[str] = None
    quality: Optional[str] = None
    radiation: Optional[str] = None
    aggravating_factors: List[str] = field(default_factory=list)
    relieving_factors: List[str] = field(default_factory=list)
    associated_symptoms: List[str] = field(default_factory=list)
    timing: Optional[str] = None
    context: Optional[str] = None
```

---

### Diagnosis

```python
@dataclass
class Diagnosis:
    name: str
    icd10_code: Optional[str] = None
    confidence: float = 1.0
    is_primary: bool = False
    is_differential: bool = False
    supporting_evidence: List[str] = field(default_factory=list)
    context: Optional[str] = None
```

---

### Drug

```python
@dataclass
class Drug:
    name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    dose: Optional[str] = None
    strength: Optional[str] = None
    route: str = "oral"
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    reason: Optional[str] = None
    context: Optional[str] = None
```

---

### SOAPNote

```python
@dataclass
class SOAPNote:
    # Subjective
    chief_complaint: str = ""
    history_of_present_illness: str = ""
    associated_symptoms: List[str] = field(default_factory=list)
    duration: Optional[str] = None
    severity: Optional[str] = None

    # Objective
    vitals: Dict[str, str] = field(default_factory=dict)
    examination_findings: List[str] = field(default_factory=list)
    significant_findings: List[str] = field(default_factory=list)

    # Assessment
    diagnoses: List[str] = field(default_factory=list)
    differential_diagnoses: List[str] = field(default_factory=list)
    clinical_impression: str = ""

    # Plan
    medications: List[Drug] = field(default_factory=list)
    investigations: List[Investigation] = field(default_factory=list)
    procedures: List[Procedure] = field(default_factory=list)
    advice: List[str] = field(default_factory=list)
    follow_up: Optional[str] = None
    referrals: List[str] = field(default_factory=list)

    # Metadata
    extracted_at: datetime = field(default_factory=datetime.now)
    confidence_score: float = 1.0
    raw_transcript: Optional[str] = None
```

---

### Differential

```python
@dataclass
class Differential:
    diagnosis: str
    icd10_code: Optional[str] = None
    probability: float = 0.5
    prior_probability: float = 0.0
    supporting_features: List[str] = field(default_factory=list)
    against_features: List[str] = field(default_factory=list)
    recommended_investigations: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    treatment_urgency: str = "routine"
```

---

### RedFlag

```python
@dataclass
class RedFlag:
    category: str
    description: str
    severity: Severity
    action_required: str
    time_critical: bool = False
    system: Optional[str] = None
```

---

### ClinicalContext

```python
@dataclass
class ClinicalContext:
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    known_conditions: List[str] = field(default_factory=list)
    current_medications: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    past_surgeries: List[str] = field(default_factory=list)
    family_history: List[str] = field(default_factory=list)
    social_history: Dict[str, str] = field(default_factory=dict)
    recent_labs: Dict[str, str] = field(default_factory=dict)
    recent_vitals: Dict[str, str] = field(default_factory=dict)
```

---

## Enums

### Severity

```python
class Severity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"
```

---

### Onset

```python
class Onset(str, Enum):
    ACUTE = "acute"
    SUBACUTE = "subacute"
    CHRONIC = "chronic"
    GRADUAL = "gradual"
    SUDDEN = "sudden"
```

---

## Constants

### India Disease Prevalence

Used as Bayesian priors in differential diagnosis:

```python
INDIA_PREVALENCE = {
    "diabetes mellitus": 0.08,      # 8%
    "hypertension": 0.25,            # 25%
    "tuberculosis": 0.002,           # 0.2%
    "dengue": 0.001,                 # 0.1%
    "malaria": 0.0005,               # 0.05%
    "ischemic heart disease": 0.06,  # 6%
    # ... 20+ more
}
```

---

### Indian Drug Brands

```python
INDIAN_DRUGS = {
    "metformin": {
        "generic": "Metformin",
        "brands": ["Glycomet", "Obimet", "Glucophage"]
    },
    "paracetamol": {
        "generic": "Paracetamol",
        "brands": ["Crocin", "Dolo", "Calpol"]
    },
    # ... 50+ more
}
```

---

### Medical Abbreviations

```python
ABBREVIATIONS = {
    "c/o": "complains of",
    "h/o": "history of",
    "k/c/o": "known case of",
    "OD": "once daily",
    "BD": "twice daily",
    "TDS": "thrice daily",
    # ... 30+ more
}
```

---

## Error Handling

All methods handle errors gracefully:

- **Missing LLM service**: Falls back to pattern matching
- **Unparseable text**: Returns partial results with confidence scores
- **Unknown drugs**: Stores name as-is without generic mapping
- **Missing vitals**: Continues with available data

---

## Version

Current version: **1.0.0**

---

## See Also

- [README.md](README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [example_usage.py](example_usage.py) - Working examples
- [integration_example.py](integration_example.py) - EMR integration
