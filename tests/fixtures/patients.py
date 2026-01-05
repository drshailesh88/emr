"""Comprehensive patient fixtures for DocAssist EMR testing."""

import random
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple
from src.models.schemas import Patient, PatientSnapshot, Medication


# ============== INDIAN NAME GENERATORS ==============

FIRST_NAMES_MALE = [
    "Ramesh", "Suresh", "Rajesh", "Amit", "Vijay", "Mohan", "Ravi", "Anil",
    "Sandeep", "Rajiv", "Ashok", "Dinesh", "Manoj", "Sanjay", "Deepak",
    "Mohammed", "Abdul", "Salman", "Arjun", "Karan", "Rahul", "Rohan",
    "Aarav", "Vivek", "Nitin", "Prakash", "Harish", "Naveen"
]

FIRST_NAMES_FEMALE = [
    "Sunita", "Geeta", "Priya", "Meena", "Rekha", "Pooja", "Anita", "Kavita",
    "Shalini", "Neha", "Radha", "Lakshmi", "Saraswati", "Fatima", "Ayesha",
    "Zainab", "Anjali", "Sneha", "Divya", "Nisha", "Preeti", "Shilpa"
]

LAST_NAMES = [
    "Kumar", "Sharma", "Verma", "Singh", "Patel", "Gupta", "Reddy", "Rao",
    "Mehta", "Shah", "Jain", "Agarwal", "Nair", "Iyer", "Khan", "Siddiqui",
    "Kapoor", "Malhotra", "Chopra", "Bansal", "Choudhary", "Desai",
    "Kulkarni", "Joshi", "Pandey", "Mishra", "Tripathi", "Yadav"
]

CITIES = [
    ("Sector 15, Noida", "201301"),
    ("Lajpat Nagar, Delhi", "110024"),
    ("Andheri West, Mumbai", "400058"),
    ("Koramangala, Bangalore", "560034"),
    ("T Nagar, Chennai", "600017"),
    ("Banjara Hills, Hyderabad", "500034"),
    ("Salt Lake, Kolkata", "700064"),
    ("Vaishali, Ghaziabad", "201010"),
    ("Powai, Mumbai", "400076"),
    ("Indiranagar, Bangalore", "560038"),
    ("Dwarka, Delhi", "110075"),
    ("Satellite, Ahmedabad", "380015"),
    ("Gomti Nagar, Lucknow", "226010"),
    ("Mansarovar, Jaipur", "302020"),
    ("Aundh, Pune", "411007"),
]


def generate_indian_name(gender: str = None) -> str:
    """Generate a realistic Indian name."""
    if gender is None:
        gender = random.choice(["M", "F"])

    if gender == "M":
        first = random.choice(FIRST_NAMES_MALE)
    else:
        first = random.choice(FIRST_NAMES_FEMALE)

    last = random.choice(LAST_NAMES)
    return f"{first} {last}"


def generate_phone_number() -> str:
    """Generate realistic Indian phone number."""
    return f"{random.choice([98, 99, 97, 96, 95, 94, 93, 91, 90, 89, 88, 87, 86, 85])}{random.randint(10000000, 99999999)}"


def generate_address() -> str:
    """Generate realistic Indian address."""
    locality, pincode = random.choice(CITIES)
    return f"{locality} - {pincode}"


def generate_uhid(patient_id: int) -> str:
    """Generate UHID for patient."""
    return f"EMR-2024-{patient_id:05d}"


# ============== COMPREHENSIVE PATIENT FIXTURES ==============

PATIENTS = {
    # Diabetic patients (various stages)
    'diabetic_elderly': Patient(
        name='Ramesh Kumar',
        age=65,
        gender='M',
        phone='9876543210',
        address='Sector 15, Noida - 201301'
    ),

    'diabetic_young': Patient(
        name='Vikram Malhotra',
        age=42,
        gender='M',
        phone='9876543220',
        address='Dwarka, Delhi - 110075'
    ),

    'diabetic_uncontrolled': Patient(
        name='Sunita Sharma',
        age=52,
        gender='F',
        phone='9876543211',
        address='Lajpat Nagar, Delhi - 110024'
    ),

    'diabetic_with_complications': Patient(
        name='Rajendra Singh',
        age=70,
        gender='M',
        phone='9876543221',
        address='Vaishali, Ghaziabad - 201010'
    ),

    # Cardiac patients
    'cardiac_af': Patient(
        name='Mohan Patel',
        age=72,
        gender='M',
        phone='9876543212',
        address='Andheri West, Mumbai - 400058'
    ),

    'post_mi': Patient(
        name='Rajiv Mehta',
        age=60,
        gender='M',
        phone='9876543213',
        address='Koramangala, Bangalore - 560034'
    ),

    'cardiac_young': Patient(
        name='Arjun Reddy',
        age=38,
        gender='M',
        phone='9876543222',
        address='Banjara Hills, Hyderabad - 500034'
    ),

    # Renal patients
    'ckd_stage_3': Patient(
        name='Geeta Verma',
        age=68,
        gender='F',
        phone='9876543214',
        address='Vaishali, Ghaziabad - 201010'
    ),

    'ckd_stage_4': Patient(
        name='Harish Nair',
        age=72,
        gender='M',
        phone='9876543223',
        address='T Nagar, Chennai - 600017'
    ),

    # Pediatric patients
    'pediatric_asthma': Patient(
        name='Aarav Sharma',
        age=8,
        gender='M',
        phone='9876543215',
        address='Powai, Mumbai - 400076'
    ),

    'pediatric_healthy': Patient(
        name='Ananya Gupta',
        age=5,
        gender='F',
        phone='9876543224',
        address='Indiranagar, Bangalore - 560038'
    ),

    'pediatric_premature': Patient(
        name='Kabir Khan',
        age=2,
        gender='M',
        phone='9876543225',
        address='Salt Lake, Kolkata - 700064'
    ),

    # Pregnant women
    'pregnant_normal': Patient(
        name='Priya Gupta',
        age=28,
        gender='F',
        phone='9876543216',
        address='Indiranagar, Bangalore - 560038'
    ),

    'pregnant_gestational_diabetes': Patient(
        name='Kavita Desai',
        age=32,
        gender='F',
        phone='9876543226',
        address='Satellite, Ahmedabad - 380015'
    ),

    'pregnant_high_risk': Patient(
        name='Fatima Siddiqui',
        age=38,
        gender='F',
        phone='9876543227',
        address='Gomti Nagar, Lucknow - 226010'
    ),

    # Allergy cases
    'multiple_allergies': Patient(
        name='Amit Kapoor',
        age=45,
        gender='M',
        phone='9876543217',
        address='Dwarka, Delhi - 110075'
    ),

    'penicillin_allergy': Patient(
        name='Rekha Joshi',
        age=50,
        gender='F',
        phone='9876543228',
        address='Aundh, Pune - 411007'
    ),

    # COPD patients
    'copd_patient': Patient(
        name='Ashok Yadav',
        age=66,
        gender='M',
        phone='9876543229',
        address='Mansarovar, Jaipur - 302020'
    ),

    # Cancer patients
    'cancer_patient': Patient(
        name='Shalini Tripathi',
        age=58,
        gender='F',
        phone='9876543230',
        address='Gomti Nagar, Lucknow - 226010'
    ),

    # Psychiatric patients
    'psychiatric_patient': Patient(
        name='Rohit Bansal',
        age=35,
        gender='M',
        phone='9876543231',
        address='Salt Lake, Kolkata - 700064'
    ),

    # Elderly polypharmacy
    'elderly_polypharmacy': Patient(
        name='Lalita Iyer',
        age=78,
        gender='F',
        phone='9876543232',
        address='T Nagar, Chennai - 600017'
    ),

    # Young healthy
    'young_healthy': Patient(
        name='Neha Chopra',
        age=25,
        gender='F',
        phone='9876543233',
        address='Koramangala, Bangalore - 560034'
    ),

    # Thyroid patient
    'hypothyroid': Patient(
        name='Pooja Agarwal',
        age=42,
        gender='F',
        phone='9876543234',
        address='Lajpat Nagar, Delhi - 110024'
    ),

    # TB patient
    'tb_patient': Patient(
        name='Mohammed Khan',
        age=35,
        gender='M',
        phone='9876543235',
        address='Andheri West, Mumbai - 400058'
    ),

    # HIV patient
    'hiv_patient': Patient(
        name='Dinesh Kulkarni',
        age=40,
        gender='M',
        phone='9876543236',
        address='Aundh, Pune - 411007'
    ),
}


# ============== PATIENT SNAPSHOTS WITH CLINICAL DATA ==============

def get_patient_by_condition(condition: str) -> Tuple[Patient, PatientSnapshot]:
    """Get patient and snapshot by condition."""

    snapshots = {
        'diabetic_elderly': PatientSnapshot(
            patient_id=1,
            uhid="EMR-2024-00001",
            demographics="Ramesh Kumar, 65M",
            active_problems=[
                "Type 2 Diabetes Mellitus",
                "Hypertension",
                "Dyslipidemia"
            ],
            current_medications=[
                Medication(drug_name="Metformin", strength="500mg", dose="1", frequency="BD", instructions="after meals"),
                Medication(drug_name="Glimepiride", strength="2mg", dose="1", frequency="OD", instructions="before breakfast"),
                Medication(drug_name="Ramipril", strength="5mg", dose="1", frequency="OD"),
                Medication(drug_name="Atorvastatin", strength="20mg", dose="1", frequency="OD", instructions="at bedtime"),
            ],
            allergies=[],
            key_labs={
                "hba1c": {"value": 7.2, "date": (date.today() - timedelta(days=90)).isoformat(), "unit": "%"},
                "fbs": {"value": 125, "date": date.today().isoformat(), "unit": "mg/dL"},
                "creatinine": {"value": 1.0, "date": date.today().isoformat(), "unit": "mg/dL"},
                "ldl": {"value": 95, "date": (date.today() - timedelta(days=90)).isoformat(), "unit": "mg/dL"},
            },
            vitals={"BP": "135/85", "Weight": "75kg", "BMI": "26.8"},
            blood_group="B+",
            on_anticoagulation=False,
            last_visit_date=date.today() - timedelta(days=30)
        ),

        'cardiac_af': PatientSnapshot(
            patient_id=3,
            uhid="EMR-2024-00003",
            demographics="Mohan Patel, 72M",
            active_problems=[
                "Atrial Fibrillation",
                "Hypertension",
                "Dyslipidemia"
            ],
            current_medications=[
                Medication(drug_name="Warfarin", strength="5mg", dose="1", frequency="OD"),
                Medication(drug_name="Metoprolol", strength="50mg", dose="1", frequency="BD"),
                Medication(drug_name="Atorvastatin", strength="40mg", dose="1", frequency="OD"),
                Medication(drug_name="Ramipril", strength="5mg", dose="1", frequency="OD"),
            ],
            allergies=[],
            key_labs={
                "inr": {"value": 2.5, "date": (date.today() - timedelta(days=7)).isoformat(), "unit": ""},
                "creatinine": {"value": 1.3, "date": date.today().isoformat(), "unit": "mg/dL"},
                "potassium": {"value": 4.5, "date": date.today().isoformat(), "unit": "mEq/L"}
            },
            vitals={"BP": "128/78", "Pulse": "Irregular, 85/min", "Weight": "70kg"},
            blood_group="A+",
            on_anticoagulation=True,
            anticoag_drug="Warfarin",
            last_visit_date=date.today() - timedelta(days=14)
        ),

        'ckd_stage_3': PatientSnapshot(
            patient_id=5,
            uhid="EMR-2024-00005",
            demographics="Geeta Verma, 68F",
            active_problems=[
                "Chronic Kidney Disease - Stage 3",
                "Hypertension",
                "Anemia of CKD"
            ],
            current_medications=[
                Medication(drug_name="Amlodipine", strength="5mg", dose="1", frequency="OD"),
                Medication(drug_name="Telmisartan", strength="40mg", dose="1", frequency="OD"),
                Medication(drug_name="Erythropoietin", strength="4000 units", dose="1", frequency="weekly", form="injection"),
                Medication(drug_name="Iron Sucrose", strength="100mg", dose="1", frequency="weekly", form="injection"),
            ],
            allergies=["Ibuprofen", "NSAIDs"],
            key_labs={
                "creatinine": {"value": 2.8, "date": date.today().isoformat(), "unit": "mg/dL"},
                "egfr": {"value": 25, "date": date.today().isoformat(), "unit": "ml/min"},
                "hemoglobin": {"value": 9.2, "date": date.today().isoformat(), "unit": "g/dL"},
                "potassium": {"value": 5.2, "date": date.today().isoformat(), "unit": "mEq/L"}
            },
            vitals={"BP": "138/88", "Weight": "58kg"},
            blood_group="B-",
            on_anticoagulation=False
        ),

        'pediatric_asthma': PatientSnapshot(
            patient_id=6,
            uhid="EMR-2024-00006",
            demographics="Aarav Sharma, 8M",
            active_problems=["Bronchial Asthma - Mild Persistent"],
            current_medications=[
                Medication(drug_name="Salbutamol", strength="100mcg", dose="2 puffs", frequency="SOS", form="inhaler"),
                Medication(drug_name="Budesonide", strength="200mcg", dose="1 puff", frequency="BD", form="inhaler"),
            ],
            allergies=[],
            key_labs={},
            vitals={"Weight": "25kg", "Height": "125cm"},
            blood_group="O+",
            on_anticoagulation=False
        ),

        'elderly_polypharmacy': PatientSnapshot(
            patient_id=22,
            uhid="EMR-2024-00022",
            demographics="Lalita Iyer, 78F",
            active_problems=[
                "Type 2 Diabetes Mellitus",
                "Hypertension",
                "Osteoarthritis",
                "Chronic Kidney Disease - Stage 3",
                "Hypothyroidism",
                "Depression",
                "Osteoporosis"
            ],
            current_medications=[
                Medication(drug_name="Metformin", strength="500mg", dose="1", frequency="BD"),
                Medication(drug_name="Glimepiride", strength="1mg", dose="1", frequency="OD"),
                Medication(drug_name="Amlodipine", strength="5mg", dose="1", frequency="OD"),
                Medication(drug_name="Telmisartan", strength="40mg", dose="1", frequency="OD"),
                Medication(drug_name="Levothyroxine", strength="75mcg", dose="1", frequency="OD"),
                Medication(drug_name="Escitalopram", strength="10mg", dose="1", frequency="OD"),
                Medication(drug_name="Calcium + Vitamin D", strength="500mg+250IU", dose="1", frequency="BD"),
                Medication(drug_name="Alendronate", strength="70mg", dose="1", frequency="weekly"),
                Medication(drug_name="Paracetamol", strength="500mg", dose="1", frequency="TDS PRN"),
                Medication(drug_name="Pantoprazole", strength="40mg", dose="1", frequency="OD"),
            ],
            allergies=["Aspirin", "NSAIDs"],
            key_labs={
                "hba1c": {"value": 7.8, "date": (date.today() - timedelta(days=60)).isoformat(), "unit": "%"},
                "creatinine": {"value": 2.2, "date": date.today().isoformat(), "unit": "mg/dL"},
                "tsh": {"value": 3.5, "date": (date.today() - timedelta(days=90)).isoformat(), "unit": "mIU/L"},
            },
            vitals={"BP": "142/88", "Weight": "52kg", "BMI": "22.3"},
            blood_group="AB+",
            on_anticoagulation=False
        ),
    }

    patient = PATIENTS.get(condition)
    snapshot = snapshots.get(condition)

    if patient and snapshot:
        return (patient, snapshot)
    return None


# ============== PATIENT GENERATORS ==============

def generate_patients(n: int, seed: int = 42) -> List[Patient]:
    """Generate n realistic random patients."""
    random.seed(seed)
    patients = []

    # Age distribution matching Indian demographics
    age_distribution = (
        [(i, 0.05) for i in range(0, 15)] +      # Children 5%
        [(i, 0.20) for i in range(15, 30)] +     # Young adults 20%
        [(i, 0.30) for i in range(30, 50)] +     # Adults 30%
        [(i, 0.30) for i in range(50, 70)] +     # Middle-aged 30%
        [(i, 0.15) for i in range(70, 90)]       # Elderly 15%
    )

    for i in range(n):
        gender = random.choice(["M", "F"])
        age = random.choices(
            [a for a, _ in age_distribution],
            weights=[w for _, w in age_distribution]
        )[0]

        patient = Patient(
            name=generate_indian_name(gender),
            age=age,
            gender=gender,
            phone=generate_phone_number(),
            address=generate_address(),
        )
        patients.append(patient)

    return patients


def generate_patient_with_condition(condition_type: str) -> Patient:
    """Generate patient with specific condition."""
    condition_templates = {
        "diabetes": lambda: Patient(
            name=generate_indian_name(),
            age=random.randint(40, 75),
            gender=random.choice(["M", "F"]),
            phone=generate_phone_number(),
            address=generate_address(),
        ),
        "cardiac": lambda: Patient(
            name=generate_indian_name(),
            age=random.randint(50, 80),
            gender="M",  # More common in males
            phone=generate_phone_number(),
            address=generate_address(),
        ),
        "pediatric": lambda: Patient(
            name=generate_indian_name(),
            age=random.randint(1, 15),
            gender=random.choice(["M", "F"]),
            phone=generate_phone_number(),
            address=generate_address(),
        ),
        "pregnant": lambda: Patient(
            name=generate_indian_name("F"),
            age=random.randint(20, 40),
            gender="F",
            phone=generate_phone_number(),
            address=generate_address(),
        ),
    }

    generator = condition_templates.get(condition_type)
    return generator() if generator else None


__all__ = [
    "PATIENTS",
    "generate_patients",
    "generate_indian_name",
    "generate_phone_number",
    "generate_address",
    "generate_uhid",
    "get_patient_by_condition",
    "generate_patient_with_condition",
]
