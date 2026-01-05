"""Extended sample prescriptions for testing various scenarios."""

from src.models.schemas import Prescription, Medication


# ============== SIMPLE PRESCRIPTIONS ==============

VIRAL_FEVER_PRESCRIPTION = Prescription(
    diagnosis=["Viral Fever"],
    medications=[
        Medication(
            drug_name="Paracetamol",
            strength="500mg",
            form="tablet",
            dose="1",
            frequency="TDS",
            duration="3 days",
            instructions="after meals, if fever >100F"
        ),
        Medication(
            drug_name="Cetirizine",
            strength="10mg",
            form="tablet",
            dose="1",
            frequency="OD",
            duration="3 days",
            instructions="at bedtime"
        )
    ],
    investigations=["CBC if fever persists >3 days"],
    advice=[
        "Rest",
        "Plenty of oral fluids",
        "Light diet",
        "Avoid cold water"
    ],
    follow_up="3 days if fever persists",
    red_flags=[
        "High fever >103F",
        "Severe headache",
        "Difficulty breathing",
        "Persistent vomiting"
    ]
)

URTI_PRESCRIPTION = Prescription(
    diagnosis=["Upper Respiratory Tract Infection"],
    medications=[
        Medication(
            drug_name="Azithromycin",
            strength="500mg",
            form="tablet",
            dose="1",
            frequency="OD",
            duration="3 days",
            instructions="1 hour before meals"
        ),
        Medication(
            drug_name="Paracetamol",
            strength="500mg",
            form="tablet",
            dose="1",
            frequency="TDS",
            duration="3 days",
            instructions="after meals, SOS for fever/pain"
        ),
        Medication(
            drug_name="Cetirizine",
            strength="10mg",
            form="tablet",
            dose="1",
            frequency="OD",
            duration="5 days",
            instructions="for runny nose"
        )
    ],
    investigations=[],
    advice=[
        "Steam inhalation twice daily",
        "Warm salt water gargles",
        "Avoid cold drinks",
        "Complete antibiotic course"
    ],
    follow_up="5 days or earlier if worsening"
)

# ============== CHRONIC DISEASE MANAGEMENT ==============

DIABETES_MAINTENANCE = Prescription(
    diagnosis=["Type 2 Diabetes Mellitus - Controlled"],
    medications=[
        Medication(
            drug_name="Metformin",
            strength="500mg",
            form="tablet",
            dose="1",
            frequency="BD",
            duration="1 month",
            instructions="after meals"
        ),
        Medication(
            drug_name="Glimepiride",
            strength="2mg",
            form="tablet",
            dose="1",
            frequency="OD",
            duration="1 month",
            instructions="before breakfast"
        )
    ],
    investigations=[
        "HbA1c",
        "Fasting Blood Sugar",
        "Kidney Function Test",
        "Lipid Profile"
    ],
    advice=[
        "Diet: Avoid sugar, refined carbs",
        "Exercise: 30 min walk daily",
        "Monitor blood sugar at home",
        "Foot care: Check feet daily",
        "Eye checkup annually"
    ],
    follow_up="1 month with reports"
)

HYPERTENSION_PRESCRIPTION = Prescription(
    diagnosis=["Hypertension - Stage 1"],
    medications=[
        Medication(
            drug_name="Amlodipine",
            strength="5mg",
            form="tablet",
            dose="1",
            frequency="OD",
            duration="1 month",
            instructions="morning, with or without food"
        ),
        Medication(
            drug_name="Telmisartan",
            strength="40mg",
            form="tablet",
            dose="1",
            frequency="OD",
            duration="1 month",
            instructions="can take with amlodipine"
        )
    ],
    investigations=[
        "ECG",
        "Kidney Function Test",
        "Electrolytes",
        "Lipid Profile"
    ],
    advice=[
        "Low salt diet (<5g/day)",
        "Weight reduction if overweight",
        "Regular exercise",
        "Stress management",
        "Monitor BP at home",
        "Limit alcohol"
    ],
    follow_up="2 weeks for BP check"
)

# ============== PRESCRIPTIONS WITH INTERACTIONS ==============

WARFARIN_ASPIRIN_INTERACTION = Prescription(
    diagnosis=["Atrial Fibrillation", "Coronary Artery Disease"],
    medications=[
        Medication(
            drug_name="Warfarin",
            strength="5mg",
            form="tablet",
            dose="1",
            frequency="OD",
            duration="ongoing",
            instructions="same time daily, INR monitoring"
        ),
        Medication(
            drug_name="Aspirin",
            strength="75mg",
            form="tablet",
            dose="1",
            frequency="OD",
            duration="ongoing",
            instructions="after breakfast"
        )
    ],
    investigations=["INR weekly initially, then monthly"],
    advice=[
        "⚠️ BLEEDING RISK: Warfarin + Aspirin interaction",
        "Watch for: bleeding gums, black stools, blood in urine",
        "Avoid NSAIDs (ibuprofen, diclofenac)",
        "Inform all doctors about warfarin",
        "Consistent vitamin K intake"
    ],
    follow_up="1 week for INR",
    red_flags=[
        "Any bleeding",
        "Severe headache",
        "Abdominal pain",
        "Vomiting blood"
    ]
)

METFORMIN_NSAID_INTERACTION = Prescription(
    diagnosis=["Type 2 Diabetes", "Osteoarthritis"],
    medications=[
        Medication(
            drug_name="Metformin",
            strength="500mg",
            dose="1",
            frequency="BD",
            duration="1 month"
        ),
        Medication(
            drug_name="Ibuprofen",
            strength="400mg",
            dose="1",
            frequency="TDS",
            duration="5 days",
            instructions="after meals"
        )
    ],
    investigations=["Kidney Function Test"],
    advice=[
        "⚠️ WARNING: NSAIDs may affect kidney function",
        "Monitor kidney function",
        "Use ibuprofen for shortest duration possible",
        "Adequate hydration"
    ],
    follow_up="1 week"
)

# ============== EMERGENCY/ACUTE PRESCRIPTIONS ==============

ACS_EMERGENCY = Prescription(
    diagnosis=["Acute Coronary Syndrome - STEMI"],
    medications=[
        Medication(
            drug_name="Aspirin",
            strength="325mg",
            dose="1",
            frequency="STAT",
            instructions="chew immediately"
        ),
        Medication(
            drug_name="Clopidogrel",
            strength="600mg",
            dose="1",
            frequency="STAT",
            instructions="loading dose"
        ),
        Medication(
            drug_name="Atorvastatin",
            strength="80mg",
            dose="1",
            frequency="STAT",
            instructions="high intensity statin"
        ),
        Medication(
            drug_name="Metoprolol",
            strength="25mg",
            dose="1",
            frequency="STAT",
            instructions="if BP permits"
        )
    ],
    investigations=[
        "⚠️ URGENT: ECG",
        "⚠️ URGENT: Troponin I/T",
        "CBC, Kidney Function, Electrolytes",
        "Echo ASAP"
    ],
    advice=[
        "🚨 EMERGENCY: Transfer to cath lab",
        "Primary PCI if within 12 hours",
        "Oxygen if SpO2 <90%",
        "IV access, continuous monitoring",
        "Inform cardiology"
    ],
    follow_up="Immediate hospitalization",
    red_flags=[
        "All ACS patients need admission",
        "Door to balloon time <90 minutes"
    ]
)

ANAPHYLAXIS_PRESCRIPTION = Prescription(
    diagnosis=["Anaphylactic Reaction"],
    medications=[
        Medication(
            drug_name="Adrenaline",
            strength="0.5mg (1:1000)",
            dose="0.3-0.5ml",
            frequency="STAT IM",
            instructions="anterolateral thigh"
        ),
        Medication(
            drug_name="Hydrocortisone",
            strength="200mg",
            dose="1",
            frequency="STAT IV",
            instructions=""
        ),
        Medication(
            drug_name="Chlorpheniramine",
            strength="10mg",
            dose="1",
            frequency="STAT IV slow",
            instructions=""
        )
    ],
    investigations=[],
    advice=[
        "🚨 EMERGENCY",
        "Airway protection",
        "100% oxygen",
        "IV fluids",
        "Observe 4-6 hours",
        "Identify trigger",
        "Prescribe EpiPen for future"
    ],
    follow_up="Allergy clinic referral"
)

# ============== PEDIATRIC PRESCRIPTIONS ==============

PEDIATRIC_GASTROENTERITIS = Prescription(
    diagnosis=["Acute Gastroenteritis"],
    medications=[
        Medication(
            drug_name="Zinc",
            strength="20mg",
            dose="1",
            frequency="OD",
            duration="14 days",
            form="dispersible tablet",
            instructions="dissolve in water"
        ),
        Medication(
            drug_name="Ondansetron",
            strength="2mg",
            dose="1",
            frequency="TDS",
            duration="2 days",
            form="syrup",
            instructions="for vomiting"
        ),
        Medication(
            drug_name="ORS",
            strength="1 sachet in 1L water",
            dose="Frequent small sips",
            frequency="After each loose stool",
            duration="till diarrhea stops"
        )
    ],
    investigations=[
        "Stool routine if blood/mucus present"
    ],
    advice=[
        "Continue breastfeeding",
        "Age-appropriate diet",
        "No antibiotics needed for viral AGE",
        "Watch for dehydration signs",
        "Handwashing"
    ],
    follow_up="If no improvement in 48 hours",
    red_flags=[
        "Blood in stools",
        "High fever",
        "Severe dehydration",
        "Lethargy",
        "Reduced urine output"
    ]
)

# ============== ALLERGY-RELATED PRESCRIPTIONS ==============

PENICILLIN_ALLERGY_UTI = Prescription(
    diagnosis=["Urinary Tract Infection"],
    medications=[
        Medication(
            drug_name="Ciprofloxacin",
            strength="500mg",
            form="tablet",
            dose="1",
            frequency="BD",
            duration="7 days",
            instructions="after meals, plenty of water"
        ),
        Medication(
            drug_name="Cranberry Extract",
            strength="500mg",
            dose="1",
            frequency="BD",
            duration="1 month"
        )
    ],
    investigations=[
        "Urine Culture & Sensitivity"
    ],
    advice=[
        "🔴 PATIENT ALLERGIC TO PENICILLIN",
        "Avoid: Amoxicillin, Ampicillin",
        "Drink 2-3 liters water daily",
        "Complete antibiotic course",
        "Void before/after intercourse"
    ],
    follow_up="7 days with culture report"
)

# ============== DOSE ADJUSTMENT SCENARIOS ==============

RENAL_DOSE_ADJUSTMENT = Prescription(
    diagnosis=["Urinary Tract Infection", "Chronic Kidney Disease - Stage 3"],
    medications=[
        Medication(
            drug_name="Ciprofloxacin",
            strength="250mg",  # Reduced dose
            form="tablet",
            dose="1",
            frequency="OD",  # Reduced frequency
            duration="10 days",
            instructions="⚠️ Dose adjusted for renal function (eGFR 28)"
        )
    ],
    investigations=[
        "Kidney Function Test",
        "Urine Culture"
    ],
    advice=[
        "⚠️ RENAL DOSE ADJUSTMENT REQUIRED",
        "eGFR: 28 ml/min - Stage 3 CKD",
        "Adequate hydration",
        "Monitor kidney function"
    ],
    follow_up="1 week"
)


# ============== HELPER FUNCTIONS ==============

def get_prescription_by_scenario(scenario: str) -> Prescription:
    """Get prescription by clinical scenario."""
    mapping = {
        "viral_fever": VIRAL_FEVER_PRESCRIPTION,
        "urti": URTI_PRESCRIPTION,
        "diabetes": DIABETES_MAINTENANCE,
        "hypertension": HYPERTENSION_PRESCRIPTION,
        "warfarin_interaction": WARFARIN_ASPIRIN_INTERACTION,
        "metformin_nsaid": METFORMIN_NSAID_INTERACTION,
        "acs": ACS_EMERGENCY,
        "anaphylaxis": ANAPHYLAXIS_PRESCRIPTION,
        "pediatric_age": PEDIATRIC_GASTROENTERITIS,
        "penicillin_allergy": PENICILLIN_ALLERGY_UTI,
        "renal_adjustment": RENAL_DOSE_ADJUSTMENT
    }

    return mapping.get(scenario, VIRAL_FEVER_PRESCRIPTION)


def get_prescriptions_with_interactions():
    """Get all prescriptions that have drug interactions."""
    return [
        WARFARIN_ASPIRIN_INTERACTION,
        METFORMIN_NSAID_INTERACTION
    ]


def get_emergency_prescriptions():
    """Get emergency prescriptions."""
    return [
        ACS_EMERGENCY,
        ANAPHYLAXIS_PRESCRIPTION
    ]


def get_all_sample_prescriptions():
    """Get all sample prescriptions."""
    return [
        VIRAL_FEVER_PRESCRIPTION,
        URTI_PRESCRIPTION,
        DIABETES_MAINTENANCE,
        HYPERTENSION_PRESCRIPTION,
        WARFARIN_ASPIRIN_INTERACTION,
        METFORMIN_NSAID_INTERACTION,
        ACS_EMERGENCY,
        ANAPHYLAXIS_PRESCRIPTION,
        PEDIATRIC_GASTROENTERITIS,
        PENICILLIN_ALLERGY_UTI,
        RENAL_DOSE_ADJUSTMENT
    ]
