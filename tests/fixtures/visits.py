"""Visit fixtures for DocAssist EMR testing."""

import random
import json
from datetime import date, datetime, timedelta
from typing import List, Dict
from src.models.schemas import Visit, Prescription, Medication, Vitals


# ============== VISIT FIXTURES ==============

VISITS = {
    'routine_diabetes_checkup': Visit(
        patient_id=1,
        visit_date=date.today(),
        chief_complaint='Routine diabetes checkup',
        clinical_notes='''
Patient is known case of Type 2 Diabetes for 5 years.
Currently on Metformin 500mg BD and Glimepiride 2mg OD.
Home blood sugar monitoring: FBS 120-140, PPBS 160-180.
No hypoglycemic episodes.
Diet compliance good, regular exercise.
No new complaints.

O/E:
- Alert and oriented
- BP: 135/85 mmHg
- Pulse: 78/min, regular
- Weight: 75kg, BMI: 26.8
- Systemic examination: Normal
        ''',
        diagnosis='Type 2 Diabetes Mellitus - Well controlled',
        prescription_json=json.dumps({
            "diagnosis": ["Type 2 Diabetes Mellitus - Well controlled"],
            "medications": [
                {"drug_name": "Metformin", "strength": "500mg", "dose": "1", "frequency": "BD", "duration": "1 month", "instructions": "after meals"},
                {"drug_name": "Glimepiride", "strength": "2mg", "dose": "1", "frequency": "OD", "duration": "1 month", "instructions": "before breakfast"}
            ],
            "investigations": ["HbA1c", "Fasting Lipid Profile", "Kidney Function Test"],
            "advice": ["Continue diet control", "Regular exercise 30 min daily", "Monitor blood sugar at home"],
            "follow_up": "1 month with reports"
        })
    ),

    'acute_chest_pain': Visit(
        patient_id=4,
        visit_date=date.today(),
        chief_complaint='Severe chest pain for 2 hours',
        clinical_notes='''
🚨 EMERGENCY CASE

60 year old male presents with severe central chest pain.
Started 2 hours ago, sudden onset while at rest.
Pain described as crushing, pressure-like, 9/10 severity.
Radiating to left arm and jaw.
Associated with profuse sweating, nausea, and anxiety.
No relief with rest.

Risk factors:
- Smoker for 30 years
- Hypertension
- Family history of CAD (father had MI at age 58)

O/E:
- Patient appears distressed, anxious, diaphoretic
- BP: 90/60 mmHg (hypotensive)
- Pulse: 110/min, regular
- SpO2: 94% on room air
- Respiratory rate: 22/min
- S3 gallop present
- Bilateral basal crepitations

IMPRESSION: Acute Coronary Syndrome - likely STEMI
        ''',
        diagnosis='Acute Coronary Syndrome - STEMI',
        prescription_json=json.dumps({
            "diagnosis": ["Acute Coronary Syndrome - STEMI"],
            "medications": [
                {"drug_name": "Aspirin", "strength": "325mg", "dose": "1", "frequency": "STAT", "instructions": "chew immediately"},
                {"drug_name": "Clopidogrel", "strength": "600mg", "dose": "1", "frequency": "STAT", "instructions": "loading dose"},
                {"drug_name": "Atorvastatin", "strength": "80mg", "dose": "1", "frequency": "STAT"},
            ],
            "investigations": ["⚠️ URGENT ECG", "⚠️ URGENT Troponin I/T", "CBC", "KFT", "Electrolytes", "Echo"],
            "advice": [
                "🚨 IMMEDIATE HOSPITALIZATION",
                "Transfer to cath lab for primary PCI",
                "Oxygen if SpO2 <90%",
                "IV access, continuous monitoring",
                "Inform cardiology immediately"
            ],
            "follow_up": "Immediate admission",
            "red_flags": ["All ACS patients require admission"]
        })
    ),

    'fever_child': Visit(
        patient_id=6,
        visit_date=date.today(),
        chief_complaint='High fever for 2 days',
        clinical_notes='''
5 year old child brought by mother with complaints of:
- High grade fever for 2 days
- Temperature 103-104°F
- Associated with body ache
- Reduced appetite
- Playful, taking fluids well
- No rash, no vomiting, no diarrhea
- Vaccination up to date

O/E:
- Temperature: 103.2°F
- Pulse: 110/min
- Respiratory rate: 24/min
- Throat: Mild congestion
- Chest: Clear
- Abdomen: Soft, no tenderness
- No signs of dehydration

IMPRESSION: Viral fever, likely viral exanthem
        ''',
        diagnosis='Viral fever',
        prescription_json=json.dumps({
            "diagnosis": ["Viral fever"],
            "medications": [
                {"drug_name": "Paracetamol", "strength": "250mg", "dose": "1", "frequency": "TDS", "duration": "3 days", "form": "syrup", "instructions": "after meals, if fever >100F"},
                {"drug_name": "Cetirizine", "strength": "5mg", "dose": "1", "frequency": "OD", "duration": "3 days", "form": "syrup", "instructions": "at bedtime"}
            ],
            "investigations": ["CBC if fever persists >3 days"],
            "advice": ["Rest", "Plenty of fluids", "Sponging if very high fever", "Light diet"],
            "follow_up": "3 days if fever persists or worsens",
            "red_flags": ["High fever >104F", "Seizures", "Difficulty breathing", "Persistent vomiting", "Lethargy"]
        })
    ),

    'antenatal_checkup': Visit(
        patient_id=7,
        visit_date=date.today(),
        chief_complaint='Routine antenatal checkup - 28 weeks',
        clinical_notes='''
28 year old primigravida at 28 weeks gestation.
Antenatal course uneventful so far.
Baby movements good.
No complaints of headache, blurred vision, or abdominal pain.
No vaginal bleeding or discharge.

O/E:
- BP: 118/76 mmHg
- Weight: 68kg (appropriate weight gain)
- Fundal height: 28cm (corresponds to dates)
- Fetal heart rate: 144/min, regular
- No pedal edema
- Urine albumin: Nil
- Urine sugar: Nil

Recent investigations:
- GCT: 148 mg/dL (borderline)
- Hemoglobin: 11.5 g/dL

IMPRESSION: Intrauterine pregnancy - 28 weeks, Gestational diabetes (diet controlled)
        ''',
        diagnosis='Intrauterine pregnancy - 28 weeks, Gestational diabetes',
        prescription_json=json.dumps({
            "diagnosis": ["Intrauterine pregnancy - 28 weeks", "Gestational diabetes (diet controlled)"],
            "medications": [
                {"drug_name": "Calcium", "strength": "500mg", "dose": "1", "frequency": "BD"},
                {"drug_name": "Iron + Folic Acid", "strength": "100mg+500mcg", "dose": "1", "frequency": "OD"},
                {"drug_name": "Vitamin D3", "strength": "60000 IU", "dose": "1", "frequency": "weekly"}
            ],
            "investigations": ["GTT (75g glucose tolerance test)", "Complete hemogram", "Urine routine"],
            "advice": [
                "Diet: Low glycemic index foods",
                "Blood sugar monitoring",
                "Fetal kick count daily",
                "Sleep on left side",
                "Continue current medications"
            ],
            "follow_up": "2 weeks with GTT report"
        })
    ),

    'follow_up_hypertension': Visit(
        patient_id=3,
        visit_date=date.today(),
        chief_complaint='Follow-up for hypertension',
        clinical_notes='''
72 year old male, known hypertensive for 10 years.
Currently on Amlodipine 5mg + Telmisartan 40mg OD.
Home BP monitoring: 130-140/80-90 mmHg.
Good medication compliance.
No postural dizziness, no chest pain, no breathlessness.
Also has Atrial Fibrillation on warfarin - last INR 2.5 (7 days ago).

O/E:
- BP: 132/84 mmHg
- Pulse: 85/min, irregular (AF)
- Weight: 70kg
- Systemic examination: Normal
- No pedal edema

IMPRESSION: Hypertension - controlled, Atrial fibrillation on warfarin
        ''',
        diagnosis='Hypertension - controlled, Atrial fibrillation',
        prescription_json=json.dumps({
            "diagnosis": ["Hypertension - controlled", "Atrial fibrillation"],
            "medications": [
                {"drug_name": "Amlodipine", "strength": "5mg", "dose": "1", "frequency": "OD", "duration": "1 month"},
                {"drug_name": "Telmisartan", "strength": "40mg", "dose": "1", "frequency": "OD", "duration": "1 month"},
                {"drug_name": "Warfarin", "strength": "5mg", "dose": "1", "frequency": "OD", "duration": "1 month"},
                {"drug_name": "Metoprolol", "strength": "50mg", "dose": "1", "frequency": "BD", "duration": "1 month"}
            ],
            "investigations": ["INR", "Kidney Function Test", "Electrolytes"],
            "advice": [
                "Continue current medications",
                "Low salt diet",
                "Monitor BP at home",
                "INR monitoring weekly initially"
            ],
            "follow_up": "1 week for INR, then monthly"
        })
    ),

    'new_patient_screening': Visit(
        patient_id=23,
        visit_date=date.today(),
        chief_complaint='General health checkup',
        clinical_notes='''
25 year old female presents for general health checkup.
No active complaints.
No significant past medical history.
Non-smoker, occasional alcohol.
Regular menstrual cycles.
No family history of diabetes, hypertension, or cardiac disease.

O/E:
- BP: 118/76 mmHg
- Pulse: 72/min, regular
- Weight: 58kg, Height: 160cm, BMI: 22.7
- Systemic examination: Normal

IMPRESSION: Healthy young adult
        ''',
        diagnosis='Healthy - routine screening',
        prescription_json=json.dumps({
            "diagnosis": ["Healthy"],
            "medications": [],
            "investigations": [
                "Complete Blood Count",
                "Fasting Blood Sugar",
                "Lipid Profile",
                "Thyroid Function Test",
                "Vitamin D",
                "Vitamin B12"
            ],
            "advice": [
                "Maintain healthy diet",
                "Regular exercise",
                "Adequate sleep",
                "Stress management"
            ],
            "follow_up": "After reports"
        })
    ),

    'copd_exacerbation': Visit(
        patient_id=20,
        visit_date=date.today(),
        chief_complaint='Increased breathlessness for 3 days',
        clinical_notes='''
66 year old male, known case of COPD for 10 years.
Presents with:
- Increased breathlessness for 3 days
- Productive cough with yellowish sputum
- Using inhalers but no relief
- Wheezing has increased
- Sleep disturbed due to cough
- Former smoker (quit 5 years ago, 30 pack-years)

O/E:
- Patient in respiratory distress
- BP: 135/88 mmHg
- Pulse: 98/min
- Respiratory rate: 26/min
- SpO2: 88% on room air
- Bilateral wheeze on auscultation
- Using accessory muscles of respiration

IMPRESSION: COPD - Acute exacerbation
        ''',
        diagnosis='COPD - Acute exacerbation',
        prescription_json=json.dumps({
            "diagnosis": ["COPD - Acute exacerbation"],
            "medications": [
                {"drug_name": "Azithromycin", "strength": "500mg", "dose": "1", "frequency": "OD", "duration": "3 days"},
                {"drug_name": "Prednisolone", "strength": "40mg", "dose": "1", "frequency": "OD", "duration": "5 days"},
                {"drug_name": "Salbutamol + Ipratropium", "strength": "100+20mcg", "dose": "2 puffs", "frequency": "QID", "form": "inhaler"},
            ],
            "investigations": ["Chest X-ray", "SpO2 monitoring", "ABG if SpO2 <90%"],
            "advice": [
                "Steam inhalation",
                "Avoid cold exposure",
                "Adequate hydration",
                "If breathlessness worsens - go to ER"
            ],
            "follow_up": "3 days",
            "red_flags": ["SpO2 <88%", "Severe breathlessness", "Confusion", "Chest pain"]
        })
    ),
}


# ============== VISIT GENERATORS ==============

def create_routine_visit(patient_id: int, visit_type: str = "diabetes") -> Visit:
    """Create a routine follow-up visit."""
    templates = {
        "diabetes": {
            "chief_complaint": "Routine diabetes checkup",
            "diagnosis": "Type 2 Diabetes Mellitus - controlled"
        },
        "hypertension": {
            "chief_complaint": "BP checkup",
            "diagnosis": "Hypertension - controlled"
        },
        "general": {
            "chief_complaint": "General checkup",
            "diagnosis": "Routine follow-up"
        }
    }

    template = templates.get(visit_type, templates["general"])

    return Visit(
        patient_id=patient_id,
        visit_date=date.today(),
        chief_complaint=template["chief_complaint"],
        clinical_notes="Routine follow-up visit. Patient stable. No new complaints.",
        diagnosis=template["diagnosis"],
    )


def create_emergency_visit(patient_id: int, emergency_type: str = "chest_pain") -> Visit:
    """Create an emergency visit."""
    emergencies = {
        "chest_pain": VISITS["acute_chest_pain"],
        "breathlessness": VISITS["copd_exacerbation"],
    }

    template = emergencies.get(emergency_type, emergencies["chest_pain"])

    return Visit(
        patient_id=patient_id,
        visit_date=template.visit_date,
        chief_complaint=template.chief_complaint,
        clinical_notes=template.clinical_notes,
        diagnosis=template.diagnosis,
        prescription_json=template.prescription_json,
    )


def generate_visit_history(patient_id: int, n_visits: int,
                          start_date: date = None,
                          visit_interval_days: int = 30) -> List[Visit]:
    """Generate realistic visit history for a patient."""
    if start_date is None:
        start_date = date.today() - timedelta(days=n_visits * visit_interval_days)

    visits = []
    visit_types = ["routine", "routine", "routine", "follow_up", "emergency"]  # Weighted

    for i in range(n_visits):
        visit_date = start_date + timedelta(days=i * visit_interval_days)
        visit_type = random.choice(visit_types)

        if visit_type == "emergency":
            visit = create_emergency_visit(patient_id)
        else:
            visit = create_routine_visit(patient_id)

        visit.visit_date = visit_date
        visit.created_at = datetime.combine(visit_date, datetime.min.time())
        visits.append(visit)

    return visits


def generate_visits_for_day(date_for_visits: date, n_patients: int = 20) -> List[Visit]:
    """Generate visits for a typical clinic day."""
    visits = []

    # Distribution: 70% routine, 20% follow-up, 10% emergency
    visit_weights = ["routine"] * 7 + ["follow_up"] * 2 + ["emergency"] * 1

    for i in range(n_patients):
        visit_type = random.choice(visit_weights)

        if visit_type == "emergency":
            visit = create_emergency_visit(patient_id=i+1)
        else:
            visit = create_routine_visit(patient_id=i+1)

        visit.visit_date = date_for_visits
        visits.append(visit)

    return visits


# ============== VITALS GENERATORS ==============

def generate_vitals(patient_id: int, visit_id: int = None,
                   is_abnormal: bool = False) -> Vitals:
    """Generate realistic vitals."""
    if is_abnormal:
        # Abnormal vitals
        return Vitals(
            patient_id=patient_id,
            visit_id=visit_id,
            bp_systolic=random.randint(150, 180),
            bp_diastolic=random.randint(95, 110),
            pulse=random.randint(95, 120),
            temperature=random.uniform(99.5, 103.0),
            spo2=random.randint(88, 94),
            respiratory_rate=random.randint(22, 28),
            weight=random.uniform(50, 90),
            blood_sugar=random.uniform(180, 300),
            sugar_type="RBS",
            recorded_at=datetime.now()
        )
    else:
        # Normal vitals
        return Vitals(
            patient_id=patient_id,
            visit_id=visit_id,
            bp_systolic=random.randint(110, 135),
            bp_diastolic=random.randint(70, 85),
            pulse=random.randint(65, 85),
            temperature=random.uniform(97.5, 99.0),
            spo2=random.randint(95, 100),
            respiratory_rate=random.randint(14, 20),
            weight=random.uniform(50, 90),
            blood_sugar=random.uniform(90, 140),
            sugar_type="RBS",
            recorded_at=datetime.now()
        )


__all__ = [
    "VISITS",
    "create_routine_visit",
    "create_emergency_visit",
    "generate_visit_history",
    "generate_visits_for_day",
    "generate_vitals",
]
