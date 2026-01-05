# Sample Patient Data - DocAssist EMR

This document describes the sample patient data seeded in the DocAssist EMR for demo and testing purposes.

## How to Seed Sample Data

```bash
# Run the seeder script
python3 seed_sample_data.py

# To reseed (will only seed if database is empty)
# Delete the database first:
rm data/clinic.db
python3 seed_sample_data.py
```

## Sample Patients Overview

### 1. Ram Kumar Sharma (EMR-2026-0001)
- **Age/Gender**: 65M
- **Location**: Delhi
- **Conditions**: Type 2 Diabetes Mellitus, Dyslipidemia
- **Visits**: 3 visits over 6 months showing disease progression and control
- **Investigations**:
  - HbA1c: 8.2% → 7.1% (improving with treatment)
  - Fasting Blood Sugar: 156 → 128 mg/dL
  - Lipid profile (abnormal)
  - Renal function (normal)
- **Medications**: Metformin 500mg BD, Atorvastatin 10mg OD
- **Use case**: Demonstrates chronic disease management, medication compliance, lab tracking

---

### 2. Priya Devi (EMR-2026-0002)
- **Age/Gender**: 52F
- **Location**: Mumbai
- **Conditions**: Essential Hypertension (Stage 2)
- **Visits**: 2 visits showing BP control
- **Investigations**: Renal function, Electrolytes
- **Procedures**: ECG (normal sinus rhythm, no LVH)
- **Medications**: Amlodipine 5mg OD
- **Use case**: Hypertension management, home BP monitoring, lifestyle modifications

---

### 3. Mohammed Ali Khan (EMR-2026-0003)
- **Age/Gender**: 58M
- **Location**: Hyderabad
- **Conditions**: Upper Respiratory Tract Infection (Viral)
- **Visits**: 1 recent visit (acute illness)
- **Investigations**: None (clinical diagnosis)
- **Medications**: Paracetamol, Cetirizine, Chlorpheniramine
- **Use case**: Acute care, symptomatic treatment, no investigations needed

---

### 4. Lakshmi Venkataraman (EMR-2026-0004)
- **Age/Gender**: 45F
- **Location**: Chennai
- **Conditions**: Coronary Artery Disease (post-PCI), Type 2 DM, Dyslipidemia
- **Visits**: 2 visits over 1 year
- **Investigations**:
  - Troponin I: 2.8 ng/mL (elevated - acute MI)
  - Total Cholesterol: 268 → improved with statin
  - LDL: 178 → 82 mg/dL
- **Procedures**:
  - ECG: ST depression in V4-V6
  - 2D Echo: EF 45%, RWMA
  - Coronary Angiography + PTCA with stenting to LAD
- **Medications**: Dual antiplatelet (Aspirin + Clopidogrel), Atorvastatin 40mg, Metoprolol, Ramipril
- **Use case**: Complex cardiac case, interventional procedure, multiple medications, lifelong management

---

### 5. Rajesh Patel (EMR-2026-0005)
- **Age/Gender**: 48M
- **Location**: Ahmedabad
- **Conditions**: Gastritis, GERD
- **Visits**: 1 visit
- **Investigations**: None (clinical diagnosis)
- **Procedures**: Upper GI Endoscopy (antral gastritis, H. pylori negative)
- **Medications**: Pantoprazole 40mg OD, Sucralfate suspension
- **Use case**: GI complaints, endoscopy, dietary advice

---

### 6. Sunita Singh (EMR-2026-0006)
- **Age/Gender**: 38F
- **Location**: Lucknow
- **Conditions**: Type 2 Diabetes Mellitus + Essential Hypertension (comorbidities)
- **Visits**: 4 visits (combination of DM and HTN follow-ups)
- **Investigations**: Complete diabetic workup + BP monitoring
- **Medications**: Metformin, Atorvastatin, Amlodipine
- **Use case**: Young patient with multiple chronic conditions, polypharmacy

---

### 7. Arun Bose (EMR-2026-0007)
- **Age/Gender**: 72M
- **Location**: Kolkata
- **Conditions**: Osteoarthritis - Bilateral Knee Joints (Grade 2)
- **Visits**: 2 visits showing symptomatic improvement
- **Investigations**:
  - Rheumatoid Factor: Negative
  - ESR: 18 mm/hr (normal)
- **Procedures**: X-ray Knee (bilateral) - Grade 2 OA changes
- **Medications**: Diclofenac + Paracetamol, Pantoprazole (gastroprotection), Calcium + Vit D3
- **Use case**: Geriatric care, chronic pain management, physiotherapy, imaging

---

### 8. Geeta Menon (EMR-2026-0008)
- **Age/Gender**: 61F
- **Location**: Bangalore
- **Conditions**: Primary Hypothyroidism
- **Visits**: 2 visits over 5 months
- **Investigations**:
  - TSH: 12.8 → 3.2 mIU/L (normalized)
  - Free T4: 0.6 → normalized
- **Medications**: Levothyroxine 50mcg OD (empty stomach)
- **Use case**: Endocrine disorder, hormone replacement, TSH monitoring

---

### 9. Vijay Reddy (EMR-2026-0009)
- **Age/Gender**: 42M
- **Location**: Pune
- **Conditions**: Upper Respiratory Tract Infection (Viral)
- **Visits**: 1 recent visit (acute illness)
- **Investigations**: None
- **Medications**: Paracetamol, Cetirizine, Chlorpheniramine
- **Use case**: Acute care (duplicate of #3 for variety)

---

### 10. Anita Deshmukh (EMR-2026-0010)
- **Age/Gender**: 55F
- **Location**: Nagpur
- **Conditions**: Type 2 Diabetes Mellitus
- **Visits**: 3 visits over 6 months
- **Investigations**: Complete diabetic workup (HbA1c, FBS, PPBS, Lipids, Renal function)
- **Medications**: Metformin, Atorvastatin
- **Use case**: Standard diabetes management (similar to #1 for testing consistency)

---

## Clinical Scenarios Covered

1. **Chronic Disease Management**: Diabetes, Hypertension (multiple patients)
2. **Acute Care**: URTI (2 patients)
3. **Cardiac Care**: Post-PCI with stent, complex medication regimen
4. **GI Issues**: Gastritis/GERD with endoscopy
5. **Musculoskeletal**: Osteoarthritis with imaging and physiotherapy
6. **Endocrine**: Hypothyroidism with hormone monitoring
7. **Polypharmacy**: Multiple medications, drug interactions
8. **Geriatric Care**: Elderly patients with age-appropriate conditions
9. **Comorbidities**: Patients with multiple chronic conditions

## Medical Realism

All sample data includes:
- ✅ Realistic Indian names from multiple regions
- ✅ Authentic Indian phone numbers (10 digits, 6-9 prefix)
- ✅ Real Indian addresses (major cities with localities)
- ✅ Clinically consistent data (diabetics have HbA1c, cardiac patients have troponin, etc.)
- ✅ Proper medication dosages (Metformin 500mg BD, Amlodipine 5mg OD, etc.)
- ✅ Indian medical shorthand ("k/c/o DM, HTN", "O/E:", "CVS - NAD")
- ✅ Abnormal investigations marked correctly
- ✅ Disease progression over time (improving/worsening)
- ✅ Follow-up schedules
- ✅ Red flags and safety warnings

## Testing Use Cases

This sample data is perfect for testing:

1. **Patient Search**: Search by name, UHID, condition
2. **RAG/AI Assistant**: Ask questions like:
   - "What was Ram Kumar's latest HbA1c?"
   - "Which patients are diabetic?"
   - "Show me Lakshmi's cardiac procedures"
3. **Prescription Generation**: View structured prescription JSON
4. **Lab Tracking**: See investigation trends over time
5. **Procedure Documentation**: ECG, Echo, Angiography, Endoscopy, X-rays
6. **Visit History**: Multiple visits with progression
7. **Clinical Decision Support**: Comorbidities, polypharmacy, drug interactions

## Statistics

- **Total Patients**: 10
- **Total Visits**: 22
- **Total Investigations**: 37
- **Total Procedures**: 6
- **Age Range**: 38-72 years
- **Gender Distribution**: 6 Female, 4 Male
- **Cities Represented**: 10 major Indian cities

## Programmatic Access

```python
from src.services.database import DatabaseService
from src.utils.sample_data import seed_database

# Initialize database
db = DatabaseService()

# Seed sample data (only if database is empty)
counts = seed_database(db)

# Get all patients
patients = db.get_all_patients()

# Get specific patient's data
patient = db.get_patient(1)  # Ram Kumar Sharma
visits = db.get_patient_visits(1)
investigations = db.get_patient_investigations(1)
procedures = db.get_patient_procedures(1)
```

---

**Note**: This sample data is for demo and testing purposes only. All patient names, phone numbers, and addresses are fictional. Any resemblance to real persons is purely coincidental.
