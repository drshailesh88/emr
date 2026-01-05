# Specialty-Specific Clinical Protocols

## Overview

Comprehensive evidence-based clinical protocols for three major medical specialties commonly seen in Indian clinical practice:

1. **Cardiology** - Cardiovascular conditions
2. **Pediatrics** - Children's health (0-18 years)
3. **OB/GYN** - Obstetrics and Gynecology

## Location

```
/home/user/emr/src/services/diagnosis/specialty_protocols/
├── __init__.py                  # Module exports
├── cardiology_protocols.py      # Cardiology protocols
├── pediatric_protocols.py       # Pediatric protocols
├── obgyn_protocols.py          # OB/GYN protocols
└── protocol_calculator.py      # Clinical calculators
```

## Features

### 1. Evidence-Based Treatment Protocols

Each specialty provides:
- **First-line medications** with dosing, frequency, duration
- **Second-line alternatives** for treatment failures or contraindications
- **Essential investigations** for diagnosis and monitoring
- **Lifestyle advice** and non-pharmacological management
- **Follow-up schedules**
- **Referral criteria** for specialist consultation

### 2. Prescription Compliance Checking

Automatically validates prescriptions against:
- Evidence-based guidelines (WHO, ICMR, IAP, FOGSI, CSI)
- Drug safety (contraindications, interactions)
- Age/pregnancy-specific considerations
- India-specific recommendations

### 3. Clinical Risk Calculators

Implements validated scoring systems:
- **CHA2DS2-VASc** - Stroke risk in atrial fibrillation
- **HAS-BLED** - Bleeding risk on anticoagulation
- **Framingham Risk Score** - 10-year CVD risk (India-adjusted)
- **Pediatric dosing** - Weight-based drug calculations
- **eGFR** - Adult (CKD-EPI) and pediatric (Schwartz)
- **Gestational age** and **EDD** calculators

### 4. Red Flag Detection

Identifies urgent/emergency conditions requiring immediate action:
- Cardiac emergencies (chest pain, severe hypertension)
- Pediatric danger signs (fast breathing, dehydration)
- Obstetric emergencies (bleeding, severe headache in pregnancy)

---

## Module Details

### 1. Cardiology Protocols

**Location**: `cardiology_protocols.py`

#### Conditions Covered

1. **Acute Coronary Syndrome**
   - STEMI (ST-Elevation MI)
   - NSTEMI (Non-ST-Elevation MI)
   - Unstable Angina
   - MONA protocol, dual antiplatelet therapy
   - Door-to-balloon time targets (<90 min)

2. **Heart Failure**
   - HFrEF (Reduced EF) - Quadruple therapy (GDMT)
   - HFpEF (Preserved EF)
   - ARNI, Beta-blockers, MRA, SGLT2i

3. **Atrial Fibrillation**
   - Rate vs rhythm control
   - Anticoagulation (NOACs vs Warfarin)
   - CHA2DS2-VASc score calculation
   - INR targets for Indians (2.0-2.5 safer)

4. **Hypertension** (India-specific)
   - Stage 1 & Stage 2 protocols
   - CCB preference for Indian population
   - Combination therapy thresholds
   - Target BP by comorbidity

#### Usage Example

```python
from src.services.diagnosis.specialty_protocols import CardiologyProtocols

cardio = CardiologyProtocols()

# Get protocol
stemi = cardio.get_protocol("stemi")
print(stemi.diagnosis)  # "STEMI (ST-Elevation Myocardial Infarction)"
print(stemi.first_line_drugs)  # Aspirin, Clopidogrel, Atorvastatin, etc.

# Check prescription compliance
prescription = {
    "medications": [
        {"drug_name": "Aspirin", "strength": "150mg"},
        {"drug_name": "Clopidogrel", "strength": "75mg"},
    ]
}
compliance = cardio.check_compliance(prescription, "stemi")
print(compliance.score)  # 70-100 (passes if >=70)

# Identify red flags
presentation = {"chief_complaint": "chest pain", "bp_systolic": 190}
red_flags = cardio.get_red_flags(presentation)
for flag in red_flags:
    print(f"[{flag.urgency}] {flag.symptom}: {flag.action}")
```

---

### 2. Pediatric Protocols

**Location**: `pediatric_protocols.py`

#### Conditions Covered

1. **Acute Gastroenteritis**
   - WHO ORS protocol (Plan A/B/C)
   - Zinc supplementation (IAP/WHO - India-specific)
   - Feeding guidelines
   - Dehydration assessment

2. **Pneumonia** (IMNCI guidelines)
   - Age-based classification (<2mo, 2mo-5y)
   - Respiratory rate criteria by age
   - High-dose Amoxicillin (80-90mg/kg/day)
   - Referral criteria (chest indrawing, danger signs)

3. **Fever in Children**
   - Dengue/malaria consideration (endemic areas)
   - Paracetamol dosing (15mg/kg)
   - Warning signs
   - **CRITICAL**: Aspirin contraindicated (Reye syndrome)

4. **Dengue (Pediatric)**
   - Critical phase monitoring (days 3-7)
   - Platelet and hematocrit monitoring
   - Warning signs (abdominal pain, bleeding)
   - NSAID avoidance

5. **Bronchiolitis, Croup, Asthma**

6. **Immunization Schedule**
   - India National Immunization Schedule (NIS)
   - BCG, OPV, Pentavalent, Rotavirus, PCV, MR, JE

#### Usage Example

```python
from src.services.diagnosis.specialty_protocols import PediatricProtocols

peds = PediatricProtocols()

# Get protocol
age_protocol = peds.get_protocol("acute_gastroenteritis")

# Check compliance (detects unsafe practices)
prescription = {
    "medications": [
        {"drug_name": "Aspirin", "strength": "75mg"}  # UNSAFE in children!
    ]
}
compliance = peds.check_compliance(prescription, "fever_child")
# Will flag CRITICAL issue: Aspirin contraindicated in children

# Red flags based on age and vitals
presentation = {
    "chief_complaint": "fever and cough",
    "respiratory_rate": 52
}
red_flags = peds.get_red_flags(presentation, age_months=8)
# Will detect: "Fast breathing (RR 52) - Pneumonia likely"

# Get immunization schedule
schedule = peds.get_immunization_schedule()
print(schedule["6 weeks"])  # DTwP, IPV, HepB, Hib, Rotavirus, PCV
```

---

### 3. OB/GYN Protocols

**Location**: `obgyn_protocols.py`

#### Conditions Covered

1. **Antenatal Care** (India guidelines)
   - Visit schedule (minimum 4, ideal 8+)
   - Investigations by trimester
   - Iron/Folic acid supplementation (India doses)
   - Tetanus toxoid vaccination
   - High-risk pregnancy identification

2. **Gestational Diabetes** (DIPSI criteria - India-specific)
   - 75g OGTT at 24-28 weeks
   - Medical Nutrition Therapy first
   - Insulin (gold standard) vs Metformin
   - Targets: FBS <95, 2h PP <120 mg/dL

3. **Preeclampsia/Eclampsia**
   - BP thresholds (≥140/90 with proteinuria)
   - Antihypertensives safe in pregnancy (Methyldopa, Labetalol, Nifedipine)
   - MgSO4 protocols (Pritchard/Zuspan)
   - **CRITICAL**: ACE-I/ARBs contraindicated (teratogenic)
   - Delivery timing

4. **Postpartum Care**
   - Breastfeeding support (exclusive for 6 months)
   - Contraception counseling
   - PPH recognition
   - Edinburgh scale (postpartum depression)

5. **Gynecological Conditions**
   - PCOS (Rotterdam criteria)
   - Menorrhagia (Tranexamic acid, Mefenamic acid)
   - Dysmenorrhea
   - Menopause (HRT counseling)

#### Usage Example

```python
from src.services.diagnosis.specialty_protocols import OBGYNProtocols

obgyn = OBGYNProtocols()

# Antenatal care protocol
anc = obgyn.get_protocol("antenatal_care")

# ANC visit schedule
visits = obgyn.get_anc_visit_schedule()
for visit in visits:
    print(f"Visit {visit.visit_number} at {visit.timing}")
    print(f"  Investigations: {visit.key_investigations}")

# CRITICAL: Pregnancy drug safety
prescription = {
    "medications": [
        {"drug_name": "Enalapril", "strength": "5mg"}  # ACE-I - TERATOGENIC!
    ]
}
compliance = obgyn.check_compliance(
    prescription,
    "antenatal_care",
    is_pregnant=True,
    trimester=2
)
# Will flag CRITICAL safety issue: ACE-I contraindicated in pregnancy

# Red flags
presentation = {"chief_complaint": "vaginal bleeding", "bp_systolic": 155}
red_flags = obgyn.get_red_flags(presentation, is_pregnant=True)
# Will detect multiple emergencies
```

---

### 4. Protocol Calculator

**Location**: `protocol_calculator.py`

#### Cardiology Calculators

```python
from src.services.diagnosis.specialty_protocols import ProtocolCalculator

calc = ProtocolCalculator()

# CHA2DS2-VASc score (stroke risk in AF)
result = calc.calculate_cha2ds2_vasc(
    age=72,
    gender="M",
    chf_history=True,
    hypertension=True,
    diabetes=True
)
# Returns: score, risk_percentage, recommendation, preferred_treatment

# HAS-BLED score (bleeding risk on anticoagulation)
result = calc.calculate_hasbled(
    age=70,
    hypertension_uncontrolled=True,
    abnormal_renal_function=True
)
# Returns: score, bleeding_risk_percentage, interpretation

# Framingham 10-year CVD risk (India-adjusted: 1.5x multiplier)
result = calc.calculate_framingham(
    age=55,
    gender="M",
    total_cholesterol=220,
    hdl=35,
    systolic_bp=150,
    smoker=True,
    diabetic=True
)
# Returns: CVDRiskResult with risk_percentage, risk_category, target_ldl
```

#### Pediatric Calculators

```python
# Weight-based pediatric dosing
dose = calc.calculate_pediatric_dose("Paracetamol", weight_kg=15)
# Returns: Dose(amount=7.5, unit="ml", frequency="TDS-QID")

dose = calc.calculate_pediatric_dose("Amoxicillin", weight_kg=12)
# High-dose: 90mg/kg/day divided TDS

# Pediatric eGFR (Schwartz formula)
egfr = calc.calculate_egfr_pediatric(creatinine_mg_dl=0.8, height_cm=120)
# Returns: 61.9 mL/min/1.73m²

# Maintenance IV fluids (4-2-1 rule)
fluids = calc.calculate_maintenance_fluids_pediatric(weight_kg=18)
# Returns: {'ml_per_hour': 58, 'ml_per_day': 1392}
```

#### OB/GYN Calculators

```python
from datetime import date

# Expected Delivery Date (Naegele's rule)
lmp = date(2024, 10, 1)
edd = calc.calculate_edd(lmp)
# Returns: 2025-07-08 (LMP + 280 days)

# Gestational age
ga = calc.calculate_gestational_age(lmp)
# Returns: {
#   'weeks': 13,
#   'days': 4,
#   'gestational_age': '13+4 weeks',
#   'trimester': 'Second',
#   'term_status': 'Preterm'
# }
```

#### Renal Calculators

```python
# Adult eGFR (CKD-EPI equation)
egfr = calc.calculate_egfr_adult(
    creatinine_mg_dl=1.5,
    age=65,
    gender="M",
    race="non-black"  # Use for Indian population
)
# Returns: 48.7 mL/min/1.73m² (CKD Stage 3)
```

---

## Safety Features

### 1. Contraindication Checking

Protocols include contraindications and will flag unsafe prescriptions:

```python
# Example: Aspirin in children
peds.check_compliance(
    {"medications": [{"drug_name": "Aspirin"}]},
    "fever_child"
)
# CRITICAL: Aspirin contraindicated (Reye syndrome)

# Example: ACE-I in pregnancy
obgyn.check_compliance(
    {"medications": [{"drug_name": "Enalapril"}]},
    "antenatal_care",
    is_pregnant=True
)
# CRITICAL: ACE-I teratogenic in pregnancy

# Example: NSAID in dengue
peds.check_compliance(
    {"medications": [{"drug_name": "Ibuprofen"}]},
    "dengue_pediatric"
)
# CRITICAL: NSAID increases bleeding risk in dengue
```

### 2. Drug Interaction Warnings

```python
# Clopidogrel + PPI interaction
compliance = cardio.check_compliance(prescription, "stemi")
# Will warn: "Clopidogrel + PPI (omeprazole) - reduced efficacy"
```

### 3. Pregnancy Category Checks

All OB/GYN protocols flag teratogenic drugs:
- **ACE inhibitors** (teratogenic)
- **ARBs** (teratogenic)
- **Warfarin** (teratogenic in T1)
- **Isotretinoin** (highly teratogenic)

---

## India-Specific Adaptations

### 1. Cardiology
- **Hypertension**: CCB (Amlodipine) preferred first-line for Indians (better response)
- **Warfarin INR**: 2.0-2.5 safer for Indians (vs 2.0-3.0 globally)
- **Framingham Risk**: 1.5x multiplier for South Asians

### 2. Pediatrics
- **Zinc supplementation**: 20mg OD x 14 days for diarrhea (IAP/WHO)
- **High-dose Amoxicillin**: 80-90mg/kg/day (India IMNCI protocol)
- **Dengue**: Endemic - always consider in fever cases
- **Malaria**: Endemic - peripheral smear in fever workup
- **NIS**: India National Immunization Schedule (BCG, OPV, Rotavirus, JE)

### 3. OB/GYN
- **DIPSI criteria**: 75g OGTT (not 2-step like US)
- **GDM targets**: FBS <95, 2h PP <120 (stricter than global)
- **Iron dosing**: 100mg elemental iron + 500mcg folic acid
- **Calcium**: 1000mg/day throughout pregnancy
- **ANC visits**: Minimum 4 (WHO), Ideal 8+ (India)

---

## Guidelines Followed

### International
- **WHO** - Essential medicines, ORS protocol, growth charts
- **ACC/AHA** - Cardiology guidelines
- **ESC** - European cardiology guidelines
- **ACOG** - Obstetrics guidelines

### India-Specific
- **ICMR** - Indian Council of Medical Research
- **RSSDI** - Research Society for Study of Diabetes in India
- **CSI** - Cardiological Society of India
- **IAP** - Indian Academy of Pediatrics
- **FOGSI** - Federation of Obstetric and Gynecological Societies of India
- **IMNCI** - Integrated Management of Neonatal and Childhood Illness
- **DIPSI** - Diabetes in Pregnancy Study Group India

---

## Data Models

### TreatmentProtocol

```python
@dataclass
class TreatmentProtocol:
    diagnosis: str
    icd10_code: Optional[str]
    first_line_drugs: List[Medication]
    second_line_drugs: List[Medication]
    investigations: List[str]
    monitoring: List[str]
    lifestyle_advice: List[str]
    follow_up_interval: str
    referral_criteria: List[str]
    contraindications: Dict[str, List[str]]
    drug_interactions: List[str]
```

### ComplianceReport

```python
@dataclass
class ComplianceReport:
    diagnosis: str
    is_compliant: bool
    issues: List[ComplianceIssue]  # severity, category, description, recommendation
    suggestions: List[str]
    score: float  # 0-100 (passing ≥70)
```

### RedFlag

```python
@dataclass
class RedFlag:
    symptom: str
    urgency: str  # EMERGENCY, URGENT, MONITOR
    action: str
```

---

## Code Statistics

- **Total Lines**: 3,596 lines of production code
- **Protocols**: 30+ condition-specific protocols
- **Calculators**: 15+ clinical calculators
- **Safety Checks**: 50+ contraindication/interaction checks

### File Breakdown

| File | Lines | Size |
|------|-------|------|
| `cardiology_protocols.py` | 915 | 34 KB |
| `obgyn_protocols.py` | 1,010 | 40 KB |
| `pediatric_protocols.py` | 858 | 32 KB |
| `protocol_calculator.py` | 765 | 23 KB |
| `__init__.py` | 48 | 1.3 KB |
| **Total** | **3,596** | **131 KB** |

---

## Integration with DocAssist EMR

These protocols integrate with the existing EMR workflow:

1. **Diagnosis Engine** → Suggests differential diagnoses
2. **Protocol Engine** → Retrieves specialty protocol
3. **Prescription Generation** → LLM generates draft using protocol
4. **Compliance Check** → Validates against evidence-based guidelines
5. **Red Flag Detection** → Alerts doctor to urgent conditions
6. **Clinical Calculators** → Embedded in UI for risk stratification

---

## Testing

All files validated:
- ✓ Python syntax check passed
- ✓ All imports resolved
- ✓ Dataclass structures validated
- ✓ Type hints verified

---

## Future Enhancements

1. **Additional Specialties**
   - Nephrology protocols (CKD, AKI, dialysis)
   - Endocrinology (thyroid, PCOS)
   - Dermatology (common skin conditions)

2. **Enhanced Calculators**
   - MELD score (liver disease)
   - APACHE II (ICU scoring)
   - WHO growth charts integration

3. **Drug Database Integration**
   - Brand-to-generic mapping
   - India-specific drug pricing
   - Availability checking

4. **AI-Powered Features**
   - LLM integration for protocol selection
   - Natural language queries ("What's first-line for STEMI?")
   - Automated compliance checking in real-time

---

## License & Attribution

These protocols are based on publicly available medical guidelines from WHO, ICMR, IAP, FOGSI, CSI, ACC/AHA, and other reputable sources. They are intended for use by qualified medical professionals as clinical decision support tools.

**Disclaimer**: These protocols are for informational purposes only. Clinical judgment should always take precedence. Always verify against current guidelines and local formularies.

---

## Contact & Contributions

For questions, updates, or contributions to these protocols:
- Ensure all additions are evidence-based
- Cite guidelines (WHO, ICMR, IAP, etc.)
- Follow India-specific adaptations where applicable
- Include safety checks and contraindications

**Last Updated**: 2026-01-05
**Version**: 1.0.0
