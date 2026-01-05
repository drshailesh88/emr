"""Extended sample patient profiles for testing various clinical scenarios."""

from datetime import date, timedelta
from src.models.schemas import Patient, PatientSnapshot, Medication


# ============== DIABETIC PATIENTS ==============

DIABETIC_CONTROLLED = Patient(
    name="Ramesh Kumar",
    age=58,
    gender="M",
    phone="9876543210",
    address="Sector 15, Noida"
)

DIABETIC_CONTROLLED_SNAPSHOT = PatientSnapshot(
    patient_id=1,
    uhid="EMR-2024-D001",
    demographics="Ramesh Kumar, 58M",
    active_problems=[
        "Type 2 Diabetes Mellitus",
        "Hypertension"
    ],
    current_medications=[
        Medication(
            drug_name="Metformin",
            strength="500mg",
            dose="1",
            frequency="BD",
            instructions="after meals"
        ),
        Medication(
            drug_name="Glimepiride",
            strength="2mg",
            dose="1",
            frequency="OD",
            instructions="before breakfast"
        ),
        Medication(
            drug_name="Ramipril",
            strength="5mg",
            dose="1",
            frequency="OD"
        )
    ],
    allergies=[],
    key_labs={
        "hba1c": {"value": 7.2, "date": (date.today() - timedelta(days=90)).isoformat(), "unit": "%"},
        "fbs": {"value": 125, "date": date.today().isoformat(), "unit": "mg/dL"},
        "creatinine": {"value": 1.0, "date": date.today().isoformat(), "unit": "mg/dL"},
        "potassium": {"value": 4.2, "date": date.today().isoformat(), "unit": "mEq/L"}
    },
    vitals={
        "BP": "135/85",
        "Weight": "75kg",
        "BMI": "26.8"
    },
    blood_group="B+",
    on_anticoagulation=False,
    last_visit_date=date.today() - timedelta(days=30)
)

DIABETIC_UNCONTROLLED = Patient(
    name="Sunita Sharma",
    age=52,
    gender="F",
    phone="9876543211",
    address="Lajpat Nagar, Delhi"
)

DIABETIC_UNCONTROLLED_SNAPSHOT = PatientSnapshot(
    patient_id=2,
    uhid="EMR-2024-D002",
    demographics="Sunita Sharma, 52F",
    active_problems=[
        "Type 2 Diabetes Mellitus - Uncontrolled",
        "Diabetic Neuropathy",
        "Obesity"
    ],
    current_medications=[
        Medication(
            drug_name="Metformin",
            strength="1000mg",
            dose="1",
            frequency="BD"
        ),
        Medication(
            drug_name="Sitagliptin",
            strength="100mg",
            dose="1",
            frequency="OD"
        ),
        Medication(
            drug_name="Pregabalin",
            strength="75mg",
            dose="1",
            frequency="OD",
            instructions="for neuropathic pain"
        )
    ],
    allergies=[],
    key_labs={
        "hba1c": {"value": 9.5, "date": (date.today() - timedelta(days=60)).isoformat(), "unit": "%"},
        "fbs": {"value": 220, "date": date.today().isoformat(), "unit": "mg/dL"},
        "ppbs": {"value": 310, "date": date.today().isoformat(), "unit": "mg/dL"}
    },
    vitals={
        "BP": "145/92",
        "Weight": "82kg",
        "BMI": "32.5"
    },
    blood_group="O+",
    on_anticoagulation=False
)

# ============== CARDIAC PATIENTS ==============

CARDIAC_AF_ON_WARFARIN = Patient(
    name="Mohan Patel",
    age=72,
    gender="M",
    phone="9876543212",
    address="Andheri West, Mumbai"
)

CARDIAC_AF_SNAPSHOT = PatientSnapshot(
    patient_id=3,
    uhid="EMR-2024-C001",
    demographics="Mohan Patel, 72M",
    active_problems=[
        "Atrial Fibrillation",
        "Hypertension",
        "Dyslipidemia"
    ],
    current_medications=[
        Medication(
            drug_name="Warfarin",
            strength="5mg",
            dose="1",
            frequency="OD"
        ),
        Medication(
            drug_name="Metoprolol",
            strength="50mg",
            dose="1",
            frequency="BD"
        ),
        Medication(
            drug_name="Atorvastatin",
            strength="40mg",
            dose="1",
            frequency="OD",
            instructions="at bedtime"
        ),
        Medication(
            drug_name="Ramipril",
            strength="5mg",
            dose="1",
            frequency="OD"
        )
    ],
    allergies=[],
    key_labs={
        "inr": {"value": 2.5, "date": (date.today() - timedelta(days=7)).isoformat(), "unit": ""},
        "creatinine": {"value": 1.3, "date": date.today().isoformat(), "unit": "mg/dL"},
        "potassium": {"value": 4.5, "date": date.today().isoformat(), "unit": "mEq/L"}
    },
    vitals={
        "BP": "128/78",
        "Pulse": "Irregular, 85/min",
        "Weight": "70kg"
    },
    blood_group="A+",
    code_status="FULL",
    on_anticoagulation=True,
    anticoag_drug="Warfarin",
    last_visit_date=date.today() - timedelta(days=14)
)

POST_MI_PATIENT = Patient(
    name="Rajiv Mehta",
    age=60,
    gender="M",
    phone="9876543213",
    address="Koramangala, Bangalore"
)

POST_MI_SNAPSHOT = PatientSnapshot(
    patient_id=4,
    uhid="EMR-2024-C002",
    demographics="Rajiv Mehta, 60M",
    active_problems=[
        "Post Myocardial Infarction (6 months ago)",
        "Hypertension",
        "Dyslipidemia"
    ],
    current_medications=[
        Medication(
            drug_name="Aspirin",
            strength="75mg",
            dose="1",
            frequency="OD"
        ),
        Medication(
            drug_name="Clopidogrel",
            strength="75mg",
            dose="1",
            frequency="OD"
        ),
        Medication(
            drug_name="Atorvastatin",
            strength="80mg",
            dose="1",
            frequency="OD"
        ),
        Medication(
            drug_name="Ramipril",
            strength="10mg",
            dose="1",
            frequency="OD"
        ),
        Medication(
            drug_name="Metoprolol",
            strength="25mg",
            dose="1",
            frequency="BD"
        )
    ],
    allergies=[],
    key_labs={
        "ldl": {"value": 65, "date": (date.today() - timedelta(days=30)).isoformat(), "unit": "mg/dL"},
        "creatinine": {"value": 0.9, "date": date.today().isoformat(), "unit": "mg/dL"}
    },
    vitals={
        "BP": "120/75",
        "Pulse": "68/min, regular",
        "Weight": "68kg"
    },
    blood_group="AB+",
    on_anticoagulation=False,
    major_events=["STEMI - Primary PCI to LAD (6 months ago)"]
)

# ============== CKD PATIENTS ==============

CKD_PATIENT = Patient(
    name="Geeta Verma",
    age=68,
    gender="F",
    phone="9876543214",
    address="Vaishali, Ghaziabad"
)

CKD_SNAPSHOT = PatientSnapshot(
    patient_id=5,
    uhid="EMR-2024-K001",
    demographics="Geeta Verma, 68F",
    active_problems=[
        "Chronic Kidney Disease - Stage 3",
        "Hypertension",
        "Anemia of CKD"
    ],
    current_medications=[
        Medication(
            drug_name="Amlodipine",
            strength="5mg",
            dose="1",
            frequency="OD"
        ),
        Medication(
            drug_name="Telmisartan",
            strength="40mg",
            dose="1",
            frequency="OD"
        ),
        Medication(
            drug_name="Erythropoietin",
            strength="4000 units",
            dose="1",
            frequency="weekly",
            form="injection"
        )
    ],
    allergies=["Ibuprofen"],
    key_labs={
        "creatinine": {"value": 2.8, "date": date.today().isoformat(), "unit": "mg/dL"},
        "egfr": {"value": 25, "date": date.today().isoformat(), "unit": "ml/min"},
        "hemoglobin": {"value": 9.2, "date": date.today().isoformat(), "unit": "g/dL"},
        "potassium": {"value": 5.2, "date": date.today().isoformat(), "unit": "mEq/L"}
    },
    vitals={
        "BP": "138/88",
        "Weight": "58kg"
    },
    blood_group="B-",
    on_anticoagulation=False
)

# ============== PEDIATRIC PATIENTS ==============

PEDIATRIC_ASTHMA = Patient(
    name="Aarav Sharma",
    age=8,
    gender="M",
    phone="9876543215",
    address="Powai, Mumbai"
)

PEDIATRIC_ASTHMA_SNAPSHOT = PatientSnapshot(
    patient_id=6,
    uhid="EMR-2024-P001",
    demographics="Aarav Sharma, 8M",
    active_problems=[
        "Bronchial Asthma - Mild Persistent"
    ],
    current_medications=[
        Medication(
            drug_name="Salbutamol",
            strength="100mcg",
            dose="2 puffs",
            frequency="SOS",
            form="inhaler",
            instructions="via spacer"
        ),
        Medication(
            drug_name="Budesonide",
            strength="200mcg",
            dose="1 puff",
            frequency="BD",
            form="inhaler",
            instructions="via spacer, rinse mouth after"
        )
    ],
    allergies=[],
    key_labs={},
    vitals={
        "Weight": "25kg",
        "Height": "125cm"
    },
    blood_group="O+",
    on_anticoagulation=False
)

# ============== PREGNANT PATIENTS ==============

ANTENATAL_PATIENT = Patient(
    name="Priya Gupta",
    age=28,
    gender="F",
    phone="9876543216",
    address="Indiranagar, Bangalore"
)

ANTENATAL_SNAPSHOT = PatientSnapshot(
    patient_id=7,
    uhid="EMR-2024-A001",
    demographics="Priya Gupta, 28F",
    active_problems=[
        "Intrauterine Pregnancy - 28 weeks",
        "Gestational Diabetes (Diet Controlled)"
    ],
    current_medications=[
        Medication(
            drug_name="Calcium",
            strength="500mg",
            dose="1",
            frequency="BD"
        ),
        Medication(
            drug_name="Iron + Folic Acid",
            strength="100mg + 500mcg",
            dose="1",
            frequency="OD"
        ),
        Medication(
            drug_name="Vitamin D3",
            strength="60000 IU",
            dose="1",
            frequency="weekly"
        )
    ],
    allergies=[],
    key_labs={
        "hemoglobin": {"value": 11.5, "date": (date.today() - timedelta(days=14)).isoformat(), "unit": "g/dL"},
        "gct": {"value": 148, "date": (date.today() - timedelta(days=30)).isoformat(), "unit": "mg/dL"}
    },
    vitals={
        "BP": "118/76",
        "Weight": "68kg",
        "Fundal_Height": "28cm"
    },
    blood_group="A+",
    on_anticoagulation=False
)

# ============== PATIENTS WITH ALLERGIES ==============

MULTIPLE_ALLERGIES_PATIENT = Patient(
    name="Amit Kapoor",
    age=45,
    gender="M",
    phone="9876543217",
    address="Dwarka, Delhi"
)

MULTIPLE_ALLERGIES_SNAPSHOT = PatientSnapshot(
    patient_id=8,
    uhid="EMR-2024-AL001",
    demographics="Amit Kapoor, 45M",
    active_problems=["Hypertension"],
    current_medications=[
        Medication(
            drug_name="Amlodipine",
            strength="5mg",
            dose="1",
            frequency="OD"
        )
    ],
    allergies=["Penicillin", "Sulfa drugs", "Aspirin"],
    key_labs={},
    vitals={
        "BP": "132/84",
        "Weight": "78kg"
    },
    blood_group="AB-",
    on_anticoagulation=False
)


# ============== HELPER FUNCTIONS ==============

def get_patient_by_condition(condition: str):
    """Get sample patient by condition."""
    mapping = {
        "diabetes_controlled": (DIABETIC_CONTROLLED, DIABETIC_CONTROLLED_SNAPSHOT),
        "diabetes_uncontrolled": (DIABETIC_UNCONTROLLED, DIABETIC_UNCONTROLLED_SNAPSHOT),
        "atrial_fibrillation": (CARDIAC_AF_ON_WARFARIN, CARDIAC_AF_SNAPSHOT),
        "post_mi": (POST_MI_PATIENT, POST_MI_SNAPSHOT),
        "ckd": (CKD_PATIENT, CKD_SNAPSHOT),
        "pediatric_asthma": (PEDIATRIC_ASTHMA, PEDIATRIC_ASTHMA_SNAPSHOT),
        "antenatal": (ANTENATAL_PATIENT, ANTENATAL_SNAPSHOT),
        "multiple_allergies": (MULTIPLE_ALLERGIES_PATIENT, MULTIPLE_ALLERGIES_SNAPSHOT)
    }

    return mapping.get(condition)


def get_all_sample_patients():
    """Get all sample patients."""
    return [
        (DIABETIC_CONTROLLED, DIABETIC_CONTROLLED_SNAPSHOT),
        (DIABETIC_UNCONTROLLED, DIABETIC_UNCONTROLLED_SNAPSHOT),
        (CARDIAC_AF_ON_WARFARIN, CARDIAC_AF_SNAPSHOT),
        (POST_MI_PATIENT, POST_MI_SNAPSHOT),
        (CKD_PATIENT, CKD_SNAPSHOT),
        (PEDIATRIC_ASTHMA, PEDIATRIC_ASTHMA_SNAPSHOT),
        (ANTENATAL_PATIENT, ANTENATAL_SNAPSHOT),
        (MULTIPLE_ALLERGIES_PATIENT, MULTIPLE_ALLERGIES_SNAPSHOT)
    ]
