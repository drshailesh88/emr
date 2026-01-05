"""Sample data seeder for DocAssist EMR with realistic Indian patient data."""

import logging
import random
import json
from datetime import date, timedelta, datetime
from typing import List

from ..models.schemas import Patient, Visit, Investigation, Procedure, Medication, Prescription

logger = logging.getLogger(__name__)


class SampleDataSeeder:
    """Creates realistic sample patient data for demo and testing."""

    # Indian names by region
    PATIENT_DATA = [
        {"name": "Ram Kumar Sharma", "age": 65, "gender": "M", "city": "Delhi"},
        {"name": "Priya Devi", "age": 52, "gender": "F", "city": "Mumbai"},
        {"name": "Mohammed Ali Khan", "age": 58, "gender": "M", "city": "Hyderabad"},
        {"name": "Lakshmi Venkataraman", "age": 45, "gender": "F", "city": "Chennai"},
        {"name": "Rajesh Patel", "age": 48, "gender": "M", "city": "Ahmedabad"},
        {"name": "Sunita Singh", "age": 38, "gender": "F", "city": "Lucknow"},
        {"name": "Arun Bose", "age": 72, "gender": "M", "city": "Kolkata"},
        {"name": "Geeta Menon", "age": 61, "gender": "F", "city": "Bangalore"},
        {"name": "Vijay Reddy", "age": 42, "gender": "M", "city": "Pune"},
        {"name": "Anita Deshmukh", "age": 55, "gender": "F", "city": "Nagpur"},
    ]

    def __init__(self, db_service):
        """Initialize seeder with database service."""
        self.db_service = db_service

    def _generate_phone(self) -> str:
        """Generate realistic Indian phone number."""
        prefix = random.choice(['98', '97', '96', '95', '94', '93', '92', '91', '90',
                               '89', '88', '87', '86', '85', '84', '83', '82', '81', '80',
                               '79', '78', '77', '76', '75', '74', '73', '72', '71', '70'])
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        return prefix + suffix

    def _generate_address(self, city: str) -> str:
        """Generate realistic Indian address."""
        localities = {
            "Delhi": ["Connaught Place", "Karol Bagh", "Dwarka", "Rohini", "Saket"],
            "Mumbai": ["Andheri West", "Bandra", "Dadar", "Borivali", "Malad"],
            "Chennai": ["T Nagar", "Anna Nagar", "Adyar", "Velachery", "Mylapore"],
            "Kolkata": ["Park Street", "Salt Lake", "Ballygunge", "Howrah", "Rajarhat"],
            "Bangalore": ["Koramangala", "Indiranagar", "Whitefield", "Jayanagar", "HSR Layout"],
            "Hyderabad": ["Banjara Hills", "Jubilee Hills", "Madhapur", "Kukatpally", "Gachibowli"],
            "Ahmedabad": ["Satellite", "Vastrapur", "Navrangpura", "Bopal", "Thaltej"],
            "Pune": ["Kothrud", "Hinjewadi", "Viman Nagar", "Aundh", "Wakad"],
            "Lucknow": ["Gomti Nagar", "Hazratganj", "Alambagh", "Indira Nagar", "Aliganj"],
            "Nagpur": ["Dharampeth", "Sadar", "Sitabuldi", "Civil Lines", "Ramdaspeth"],
        }

        locality = random.choice(localities.get(city, ["Main Road"]))
        street = f"{random.randint(1, 999)}, Sector {random.randint(1, 50)}"
        return f"{street}, {locality}, {city}"

    def _create_diabetic_patient_data(self, patient_id: int, age: int, gender: str) -> dict:
        """Create comprehensive data for a diabetic patient."""
        visits = []
        investigations = []
        procedures = []

        # Visit 1: Initial diagnosis (6 months ago)
        visit_date_1 = date.today() - timedelta(days=180)

        # HbA1c - elevated
        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="HbA1c",
            result="8.2",
            unit="%",
            reference_range="4.0-5.6",
            test_date=visit_date_1,
            is_abnormal=True
        ))

        # FBS - elevated
        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="Fasting Blood Sugar",
            result="156",
            unit="mg/dL",
            reference_range="70-100",
            test_date=visit_date_1,
            is_abnormal=True
        ))

        # PPBS
        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="Post Prandial Blood Sugar",
            result="224",
            unit="mg/dL",
            reference_range="< 140",
            test_date=visit_date_1,
            is_abnormal=True
        ))

        # Lipid profile
        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="Total Cholesterol",
            result="215",
            unit="mg/dL",
            reference_range="< 200",
            test_date=visit_date_1,
            is_abnormal=True
        ))

        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="LDL Cholesterol",
            result="138",
            unit="mg/dL",
            reference_range="< 100",
            test_date=visit_date_1,
            is_abnormal=True
        ))

        # Renal function
        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="Serum Creatinine",
            result="1.1",
            unit="mg/dL",
            reference_range="0.6-1.2",
            test_date=visit_date_1,
            is_abnormal=False
        ))

        prescription_1 = Prescription(
            diagnosis=["Type 2 Diabetes Mellitus (Newly diagnosed)", "Dyslipidemia"],
            medications=[
                Medication(
                    drug_name="Metformin",
                    strength="500mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="3 months",
                    instructions="after meals"
                ),
                Medication(
                    drug_name="Atorvastatin",
                    strength="10mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="3 months",
                    instructions="at bedtime"
                ),
            ],
            investigations=["HbA1c after 3 months", "Lipid profile after 3 months"],
            advice=[
                "Diet: Low sugar, low fat diet",
                "Exercise: 30 min walk daily",
                "Monitor blood sugar at home",
                "Weight reduction target: 5kg in 3 months"
            ],
            follow_up="3 months",
            red_flags=["Severe hypoglycemia (sweating, tremors, confusion)", "Chest pain", "Breathlessness"]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date_1,
            chief_complaint="Increased thirst and frequent urination x 2 months",
            clinical_notes=f"{age}{gender}, k/c/o nil. C/o polyuria, polydipsia x 2 months. "
                          f"O/E: Wt 78kg, BP 136/84. CVS, RS - NAD. Per abdomen - soft, no organomegaly.",
            diagnosis="Type 2 Diabetes Mellitus (Newly diagnosed), Dyslipidemia",
            prescription_json=prescription_1.model_dump_json()
        ))

        # Visit 2: Follow-up (3 months ago)
        visit_date_2 = date.today() - timedelta(days=90)

        # Follow-up HbA1c - improved
        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="HbA1c",
            result="7.1",
            unit="%",
            reference_range="4.0-5.6",
            test_date=visit_date_2,
            is_abnormal=True
        ))

        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="Fasting Blood Sugar",
            result="128",
            unit="mg/dL",
            reference_range="70-100",
            test_date=visit_date_2,
            is_abnormal=True
        ))

        prescription_2 = Prescription(
            diagnosis=["Type 2 Diabetes Mellitus - controlled on metformin", "Dyslipidemia"],
            medications=[
                Medication(
                    drug_name="Metformin",
                    strength="500mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="3 months",
                    instructions="after meals"
                ),
                Medication(
                    drug_name="Atorvastatin",
                    strength="10mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="3 months",
                    instructions="at bedtime"
                ),
            ],
            investigations=["HbA1c after 3 months", "Lipid profile after 3 months"],
            advice=[
                "Continue diet and exercise",
                "Good compliance, continue same medications",
                "Monitor blood sugar monthly"
            ],
            follow_up="3 months",
            red_flags=[]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date_2,
            chief_complaint="Follow-up for diabetes mellitus",
            clinical_notes=f"{age}{gender}, k/c/o DM on metformin. Compliance good. No hypoglycemic episodes. "
                          f"Wt 74kg (lost 4kg). BP 128/78. Feeling better.",
            diagnosis="Type 2 Diabetes Mellitus - controlled on metformin",
            prescription_json=prescription_2.model_dump_json()
        ))

        # Visit 3: Recent (2 weeks ago)
        visit_date_3 = date.today() - timedelta(days=14)

        prescription_3 = Prescription(
            diagnosis=["Type 2 Diabetes Mellitus - well controlled"],
            medications=[
                Medication(
                    drug_name="Metformin",
                    strength="500mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="3 months",
                    instructions="after meals"
                ),
                Medication(
                    drug_name="Atorvastatin",
                    strength="10mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="3 months",
                    instructions="at bedtime"
                ),
            ],
            investigations=["HbA1c after 3 months"],
            advice=["Excellent progress", "Continue current regimen"],
            follow_up="3 months",
            red_flags=[]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date_3,
            chief_complaint="Routine follow-up for diabetes",
            clinical_notes=f"{age}{gender}, k/c/o DM on metformin. Feeling well. No complaints. "
                          f"Wt 72kg. BP 124/76. Excellent compliance.",
            diagnosis="Type 2 Diabetes Mellitus - well controlled",
            prescription_json=prescription_3.model_dump_json()
        ))

        return {"visits": visits, "investigations": investigations, "procedures": procedures}

    def _create_hypertensive_patient_data(self, patient_id: int, age: int, gender: str) -> dict:
        """Create comprehensive data for a hypertensive patient."""
        visits = []
        investigations = []
        procedures = []

        # Visit 1: Initial presentation (4 months ago)
        visit_date_1 = date.today() - timedelta(days=120)

        # ECG
        procedures.append(Procedure(
            patient_id=patient_id,
            procedure_name="ECG",
            details="12-lead ECG",
            procedure_date=visit_date_1,
            notes="Sinus rhythm, rate 78/min. No ST-T changes. LVH criteria not met."
        ))

        # Labs
        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="Serum Creatinine",
            result="1.0",
            unit="mg/dL",
            reference_range="0.6-1.2",
            test_date=visit_date_1,
            is_abnormal=False
        ))

        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="Serum Potassium",
            result="4.2",
            unit="mEq/L",
            reference_range="3.5-5.0",
            test_date=visit_date_1,
            is_abnormal=False
        ))

        prescription_1 = Prescription(
            diagnosis=["Essential Hypertension - Stage 2"],
            medications=[
                Medication(
                    drug_name="Amlodipine",
                    strength="5mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="1 month",
                    instructions="morning"
                ),
            ],
            investigations=["Renal function after 1 month", "Lipid profile"],
            advice=[
                "Low salt diet (< 5g/day)",
                "Regular exercise",
                "Reduce stress",
                "Monitor BP at home - maintain diary"
            ],
            follow_up="1 month",
            red_flags=["Severe headache", "Chest pain", "Breathlessness", "Blurred vision"]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date_1,
            chief_complaint="Headache and dizziness x 1 week",
            clinical_notes=f"{age}{gender}, k/c/o nil. C/o headache, occipital, worse in morning. Dizziness on standing. "
                          f"O/E: BP 168/102 (avg of 3 readings). PR 78/min regular. CVS, RS - NAD. CNS - NAD.",
            diagnosis="Essential Hypertension - Stage 2",
            prescription_json=prescription_1.model_dump_json()
        ))

        # Visit 2: Follow-up (3 months ago)
        visit_date_2 = date.today() - timedelta(days=90)

        prescription_2 = Prescription(
            diagnosis=["Essential Hypertension - controlled on amlodipine"],
            medications=[
                Medication(
                    drug_name="Amlodipine",
                    strength="5mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="3 months",
                    instructions="morning"
                ),
            ],
            investigations=["Renal function after 3 months"],
            advice=["Continue current treatment", "Good BP control", "Continue lifestyle modifications"],
            follow_up="3 months",
            red_flags=[]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date_2,
            chief_complaint="Follow-up for hypertension",
            clinical_notes=f"{age}{gender}, k/c/o HTN on amlodipine 5mg OD. No headaches now. Feeling well. "
                          f"Home BP readings: 128-136/78-84. O/E: BP 132/80. PR 72/min.",
            diagnosis="Essential Hypertension - controlled",
            prescription_json=prescription_2.model_dump_json()
        ))

        return {"visits": visits, "investigations": investigations, "procedures": procedures}

    def _create_urti_patient_data(self, patient_id: int, age: int, gender: str) -> dict:
        """Create data for acute URTI patient."""
        visits = []
        investigations = []
        procedures = []

        visit_date = date.today() - timedelta(days=3)

        prescription = Prescription(
            diagnosis=["Upper Respiratory Tract Infection (Viral)"],
            medications=[
                Medication(
                    drug_name="Paracetamol",
                    strength="650mg",
                    form="tablet",
                    dose="1",
                    frequency="TDS",
                    duration="5 days",
                    instructions="after meals, SOS for fever"
                ),
                Medication(
                    drug_name="Cetirizine",
                    strength="10mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="5 days",
                    instructions="at bedtime"
                ),
                Medication(
                    drug_name="Chlorpheniramine Maleate",
                    strength="4mg",
                    form="tablet",
                    dose="1",
                    frequency="TDS",
                    duration="5 days",
                    instructions="after meals"
                ),
            ],
            investigations=[],
            advice=[
                "Plenty of fluids",
                "Steam inhalation twice daily",
                "Avoid cold foods/drinks",
                "Rest"
            ],
            follow_up="If not better in 5 days",
            red_flags=["High fever > 3 days", "Severe throat pain", "Difficulty breathing"]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date,
            chief_complaint="Runny nose, sore throat, cough x 2 days",
            clinical_notes=f"{age}{gender}, k/c/o nil. C/o rhinorrhea, nasal congestion, sore throat, dry cough x 2 days. "
                          f"Fever (low grade). O/E: Temp 99.2°F. Throat - congested, no exudate. "
                          f"RS - clear, no wheeze. CVS - NAD.",
            diagnosis="Upper Respiratory Tract Infection (Viral)",
            prescription_json=prescription.model_dump_json()
        ))

        return {"visits": visits, "investigations": investigations, "procedures": procedures}

    def _create_cardiac_patient_data(self, patient_id: int, age: int, gender: str) -> dict:
        """Create data for cardiac patient with CAD."""
        visits = []
        investigations = []
        procedures = []

        # Visit 1: Presentation with chest pain (1 year ago)
        visit_date_1 = date.today() - timedelta(days=365)

        # ECG
        procedures.append(Procedure(
            patient_id=patient_id,
            procedure_name="ECG",
            details="12-lead ECG",
            procedure_date=visit_date_1,
            notes="ST depression in V4-V6, suggestive of ischemia"
        ))

        # Echo
        procedures.append(Procedure(
            patient_id=patient_id,
            procedure_name="2D Echocardiography",
            details="Transthoracic echo",
            procedure_date=visit_date_1,
            notes="Mild LV dysfunction, EF 45%. Regional wall motion abnormality in anterolateral wall. "
                  "Mild MR. Other valves normal."
        ))

        # Angiography
        procedures.append(Procedure(
            patient_id=patient_id,
            procedure_name="Coronary Angiography",
            details="CAG via femoral approach",
            procedure_date=visit_date_1,
            notes="LAD - 80% stenosis at mid segment. LCx - 50% stenosis. RCA - Normal. "
                  "PTCA + stenting to LAD done successfully."
        ))

        # Labs
        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="Troponin I",
            result="2.8",
            unit="ng/mL",
            reference_range="< 0.04",
            test_date=visit_date_1,
            is_abnormal=True
        ))

        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="Total Cholesterol",
            result="268",
            unit="mg/dL",
            reference_range="< 200",
            test_date=visit_date_1,
            is_abnormal=True
        ))

        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="LDL Cholesterol",
            result="178",
            unit="mg/dL",
            reference_range="< 100",
            test_date=visit_date_1,
            is_abnormal=True
        ))

        prescription_1 = Prescription(
            diagnosis=[
                "Coronary Artery Disease - LAD 80% stenosis",
                "Post PTCA + Stenting to LAD",
                "Type 2 Diabetes Mellitus",
                "Dyslipidemia"
            ],
            medications=[
                Medication(
                    drug_name="Aspirin",
                    strength="150mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="lifelong",
                    instructions="after meals"
                ),
                Medication(
                    drug_name="Clopidogrel",
                    strength="75mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="1 year",
                    instructions="after meals"
                ),
                Medication(
                    drug_name="Atorvastatin",
                    strength="40mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="lifelong",
                    instructions="at bedtime"
                ),
                Medication(
                    drug_name="Metoprolol",
                    strength="25mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="lifelong",
                    instructions="after meals"
                ),
                Medication(
                    drug_name="Ramipril",
                    strength="2.5mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="lifelong",
                    instructions="morning"
                ),
            ],
            investigations=["Lipid profile after 1 month", "Renal function after 1 month"],
            advice=[
                "Strict diet control - low fat, low salt",
                "Regular exercise as tolerated",
                "Smoking cessation (if applicable)",
                "Strict medication compliance"
            ],
            follow_up="1 month",
            red_flags=["Chest pain", "Breathlessness", "Palpitations", "Severe fatigue"]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date_1,
            chief_complaint="Chest pain x 4 hours",
            clinical_notes=f"{age}{gender}, k/c/o DM, HTN. C/o chest pain, retrosternal, radiating to left arm, "
                          f"started 4 hrs ago, 8/10 severity, associated with sweating. O/E: BP 154/96, PR 98/min. "
                          f"CVS - S1 S2 normal. RS - clear. Per abd - soft.",
            diagnosis="Coronary Artery Disease - Acute Coronary Syndrome",
            prescription_json=prescription_1.model_dump_json()
        ))

        # Visit 2: Follow-up (6 months ago)
        visit_date_2 = date.today() - timedelta(days=180)

        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="LDL Cholesterol",
            result="82",
            unit="mg/dL",
            reference_range="< 100",
            test_date=visit_date_2,
            is_abnormal=False
        ))

        prescription_2 = Prescription(
            diagnosis=["Post PCI - LAD stent", "CAD - stable", "Type 2 DM", "Dyslipidemia"],
            medications=[
                Medication(
                    drug_name="Aspirin",
                    strength="150mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="3 months",
                    instructions="after meals"
                ),
                Medication(
                    drug_name="Clopidogrel",
                    strength="75mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="3 months",
                    instructions="after meals"
                ),
                Medication(
                    drug_name="Atorvastatin",
                    strength="40mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="3 months",
                    instructions="at bedtime"
                ),
                Medication(
                    drug_name="Metoprolol",
                    strength="25mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="3 months",
                    instructions="after meals"
                ),
                Medication(
                    drug_name="Ramipril",
                    strength="2.5mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="3 months",
                    instructions="morning"
                ),
            ],
            investigations=["TMT after 3 months"],
            advice=["Continue all medications", "Doing well", "No chest pain"],
            follow_up="3 months",
            red_flags=[]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date_2,
            chief_complaint="Follow-up post PCI",
            clinical_notes=f"{age}{gender}, k/c/o CAD s/p PCI to LAD, DM, HTN. No chest pain. "
                          f"Good exercise tolerance. Compliance good. O/E: BP 128/76, PR 68/min. CVS, RS - NAD.",
            diagnosis="Post PCI - LAD stent, CAD - stable",
            prescription_json=prescription_2.model_dump_json()
        ))

        return {"visits": visits, "investigations": investigations, "procedures": procedures}

    def _create_gastritis_patient_data(self, patient_id: int, age: int, gender: str) -> dict:
        """Create data for gastritis patient."""
        visits = []
        investigations = []
        procedures = []

        visit_date = date.today() - timedelta(days=7)

        # Upper GI Endoscopy (if older patient)
        if age > 50:
            procedures.append(Procedure(
                patient_id=patient_id,
                procedure_name="Upper GI Endoscopy",
                details="Diagnostic endoscopy",
                procedure_date=visit_date - timedelta(days=2),
                notes="Antral gastritis, no ulcer. CLO test negative for H. pylori."
            ))

        prescription = Prescription(
            diagnosis=["Gastritis", "Gastroesophageal Reflux Disease"],
            medications=[
                Medication(
                    drug_name="Pantoprazole",
                    strength="40mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="4 weeks",
                    instructions="30 min before breakfast"
                ),
                Medication(
                    drug_name="Sucralfate",
                    strength="1g",
                    form="suspension",
                    dose="10ml",
                    frequency="TDS",
                    duration="2 weeks",
                    instructions="before meals"
                ),
            ],
            investigations=[],
            advice=[
                "Avoid spicy, oily foods",
                "Avoid tea, coffee, alcohol",
                "Small frequent meals",
                "Elevate head end of bed",
                "Avoid late night meals"
            ],
            follow_up="2 weeks",
            red_flags=["Severe pain", "Vomiting blood", "Black stools", "Difficulty swallowing"]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date,
            chief_complaint="Burning sensation in chest and upper abdomen x 2 weeks",
            clinical_notes=f"{age}{gender}, k/c/o nil. C/o burning epigastric pain, worse on empty stomach, "
                          f"heartburn, acid reflux. O/E: Epigastric tenderness present. Per abd - soft, no organomegaly.",
            diagnosis="Gastritis, Gastroesophageal Reflux Disease",
            prescription_json=prescription.model_dump_json()
        ))

        return {"visits": visits, "investigations": investigations, "procedures": procedures}

    def _create_arthritis_patient_data(self, patient_id: int, age: int, gender: str) -> dict:
        """Create data for osteoarthritis patient."""
        visits = []
        investigations = []
        procedures = []

        # Visit 1: Initial presentation (3 months ago)
        visit_date_1 = date.today() - timedelta(days=90)

        # X-ray
        procedures.append(Procedure(
            patient_id=patient_id,
            procedure_name="X-ray Knee (Both) AP/Lat",
            details="Digital X-ray",
            procedure_date=visit_date_1,
            notes="Bilateral knee joint space narrowing, osteophytes, sclerosis. Suggestive of Grade 2 OA."
        ))

        # Labs
        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="Rheumatoid Factor",
            result="Negative",
            unit="",
            reference_range="Negative",
            test_date=visit_date_1,
            is_abnormal=False
        ))

        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="ESR",
            result="18",
            unit="mm/hr",
            reference_range="0-20",
            test_date=visit_date_1,
            is_abnormal=False
        ))

        prescription_1 = Prescription(
            diagnosis=["Osteoarthritis - Bilateral Knee Joints (Grade 2)"],
            medications=[
                Medication(
                    drug_name="Diclofenac + Paracetamol",
                    strength="50mg + 325mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="2 weeks",
                    instructions="after meals"
                ),
                Medication(
                    drug_name="Pantoprazole",
                    strength="40mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="2 weeks",
                    instructions="before breakfast (gastric protection)"
                ),
                Medication(
                    drug_name="Calcium + Vitamin D3",
                    strength="500mg + 250 IU",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="3 months",
                    instructions="after meals"
                ),
            ],
            investigations=[],
            advice=[
                "Weight reduction (if overweight)",
                "Physiotherapy - quadriceps strengthening exercises",
                "Hot water fomentation",
                "Avoid squatting, climbing stairs",
                "Use knee cap if needed"
            ],
            follow_up="2 weeks",
            red_flags=["Severe pain", "Swelling", "Locking of joint", "Inability to bear weight"]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date_1,
            chief_complaint="Bilateral knee pain x 6 months, worse on walking",
            clinical_notes=f"{age}{gender}, k/c/o nil. C/o bilateral knee pain, worse on climbing stairs, "
                          f"morning stiffness x 15 min. O/E: Local examination knee - no swelling, warmth. "
                          f"Tenderness on medial joint line. Crepitus present. ROM - restricted.",
            diagnosis="Osteoarthritis - Bilateral Knee Joints",
            prescription_json=prescription_1.model_dump_json()
        ))

        # Visit 2: Follow-up (6 weeks ago)
        visit_date_2 = date.today() - timedelta(days=42)

        prescription_2 = Prescription(
            diagnosis=["Osteoarthritis - Bilateral Knee Joints - improved"],
            medications=[
                Medication(
                    drug_name="Diclofenac + Paracetamol",
                    strength="50mg + 325mg",
                    form="tablet",
                    dose="1",
                    frequency="SOS",
                    duration="1 month",
                    instructions="after meals, only if pain"
                ),
                Medication(
                    drug_name="Calcium + Vitamin D3",
                    strength="500mg + 250 IU",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="3 months",
                    instructions="after meals"
                ),
            ],
            investigations=[],
            advice=["Continue physiotherapy", "Doing better", "Pain reduced significantly"],
            follow_up="1 month",
            red_flags=[]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date_2,
            chief_complaint="Follow-up for knee osteoarthritis",
            clinical_notes=f"{age}{gender}, k/c/o OA both knees. Compliance good. Physiotherapy ongoing. "
                          f"Pain much better. O/E: Knee - no acute signs. ROM improved.",
            diagnosis="Osteoarthritis - Bilateral Knee Joints - improved",
            prescription_json=prescription_2.model_dump_json()
        ))

        return {"visits": visits, "investigations": investigations, "procedures": procedures}

    def _create_thyroid_patient_data(self, patient_id: int, age: int, gender: str) -> dict:
        """Create data for hypothyroid patient."""
        visits = []
        investigations = []
        procedures = []

        # Visit 1: Diagnosis (5 months ago)
        visit_date_1 = date.today() - timedelta(days=150)

        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="TSH",
            result="12.8",
            unit="mIU/L",
            reference_range="0.5-5.0",
            test_date=visit_date_1,
            is_abnormal=True
        ))

        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="Free T4",
            result="0.6",
            unit="ng/dL",
            reference_range="0.8-1.8",
            test_date=visit_date_1,
            is_abnormal=True
        ))

        prescription_1 = Prescription(
            diagnosis=["Primary Hypothyroidism"],
            medications=[
                Medication(
                    drug_name="Levothyroxine",
                    strength="50mcg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="3 months",
                    instructions="empty stomach in morning, 30 min before food"
                ),
            ],
            investigations=["Thyroid function test after 6 weeks"],
            advice=[
                "Take medication regularly at same time",
                "Empty stomach - 30 min before breakfast",
                "Lifelong treatment required"
            ],
            follow_up="6 weeks",
            red_flags=["Palpitations", "Severe fatigue", "Chest pain"]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date_1,
            chief_complaint="Fatigue, weight gain, cold intolerance x 3 months",
            clinical_notes=f"{age}{gender}, k/c/o nil. C/o easy fatiguability, weight gain (5kg in 3 months), "
                          f"cold intolerance, constipation. O/E: Pulse 58/min, BP 118/74. No goiter palpable.",
            diagnosis="Primary Hypothyroidism",
            prescription_json=prescription_1.model_dump_json()
        ))

        # Visit 2: Follow-up (3 months ago)
        visit_date_2 = date.today() - timedelta(days=90)

        investigations.append(Investigation(
            patient_id=patient_id,
            test_name="TSH",
            result="3.2",
            unit="mIU/L",
            reference_range="0.5-5.0",
            test_date=visit_date_2,
            is_abnormal=False
        ))

        prescription_2 = Prescription(
            diagnosis=["Primary Hypothyroidism - controlled on levothyroxine"],
            medications=[
                Medication(
                    drug_name="Levothyroxine",
                    strength="50mcg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="6 months",
                    instructions="empty stomach in morning, 30 min before food"
                ),
            ],
            investigations=["Thyroid function test after 6 months"],
            advice=["Excellent response to treatment", "Continue same dose"],
            follow_up="6 months",
            red_flags=[]
        )

        visits.append(Visit(
            patient_id=patient_id,
            visit_date=visit_date_2,
            chief_complaint="Follow-up for hypothyroidism",
            clinical_notes=f"{age}{gender}, k/c/o hypothyroidism on levothyroxine 50mcg. Feeling much better. "
                          f"Fatigue improved. No complaints. Compliance good.",
            diagnosis="Primary Hypothyroidism - controlled",
            prescription_json=prescription_2.model_dump_json()
        ))

        return {"visits": visits, "investigations": investigations, "procedures": procedures}

    def seed(self) -> dict:
        """Seed the database with sample patient data.

        Returns:
            Dictionary with counts of created records
        """
        logger.info("Starting sample data seeding...")

        counts = {
            "patients": 0,
            "visits": 0,
            "investigations": 0,
            "procedures": 0
        }

        for idx, patient_data in enumerate(self.PATIENT_DATA):
            # Create patient
            patient = Patient(
                name=patient_data["name"],
                age=patient_data["age"],
                gender=patient_data["gender"],
                phone=self._generate_phone(),
                address=self._generate_address(patient_data["city"])
            )

            created_patient = self.db_service.add_patient(patient)
            counts["patients"] += 1
            logger.info(f"Created patient: {created_patient.name} (UHID: {created_patient.uhid})")

            # Generate clinical data based on patient profile
            clinical_data = None

            # Patient 1: Diabetic (Ram Kumar Sharma - 65M)
            if idx == 0:
                clinical_data = self._create_diabetic_patient_data(
                    created_patient.id, patient_data["age"], patient_data["gender"]
                )

            # Patient 2: Hypertensive (Priya Devi - 52F)
            elif idx == 1:
                clinical_data = self._create_hypertensive_patient_data(
                    created_patient.id, patient_data["age"], patient_data["gender"]
                )

            # Patient 3: URTI (Mohammed Ali Khan - 58M)
            elif idx == 2:
                clinical_data = self._create_urti_patient_data(
                    created_patient.id, patient_data["age"], patient_data["gender"]
                )

            # Patient 4: Cardiac patient (Lakshmi Venkataraman - 45F)
            elif idx == 3:
                clinical_data = self._create_cardiac_patient_data(
                    created_patient.id, patient_data["age"], patient_data["gender"]
                )

            # Patient 5: Gastritis (Rajesh Patel - 48M)
            elif idx == 4:
                clinical_data = self._create_gastritis_patient_data(
                    created_patient.id, patient_data["age"], patient_data["gender"]
                )

            # Patient 6: Diabetic + Hypertensive (Sunita Singh - 38F)
            elif idx == 5:
                diabetic_data = self._create_diabetic_patient_data(
                    created_patient.id, patient_data["age"], patient_data["gender"]
                )
                hypertensive_data = self._create_hypertensive_patient_data(
                    created_patient.id, patient_data["age"], patient_data["gender"]
                )
                # Merge the two datasets
                clinical_data = {
                    "visits": diabetic_data["visits"] + hypertensive_data["visits"],
                    "investigations": diabetic_data["investigations"] + hypertensive_data["investigations"],
                    "procedures": diabetic_data["procedures"] + hypertensive_data["procedures"]
                }

            # Patient 7: Arthritis (Arun Bose - 72M)
            elif idx == 6:
                clinical_data = self._create_arthritis_patient_data(
                    created_patient.id, patient_data["age"], patient_data["gender"]
                )

            # Patient 8: Hypothyroid (Geeta Menon - 61F)
            elif idx == 7:
                clinical_data = self._create_thyroid_patient_data(
                    created_patient.id, patient_data["age"], patient_data["gender"]
                )

            # Patient 9: URTI (Vijay Reddy - 42M)
            elif idx == 8:
                clinical_data = self._create_urti_patient_data(
                    created_patient.id, patient_data["age"], patient_data["gender"]
                )

            # Patient 10: Diabetic (Anita Deshmukh - 55F)
            elif idx == 9:
                clinical_data = self._create_diabetic_patient_data(
                    created_patient.id, patient_data["age"], patient_data["gender"]
                )

            # Add all visits, investigations, procedures
            if clinical_data:
                for visit in clinical_data["visits"]:
                    self.db_service.add_visit(visit)
                    counts["visits"] += 1

                for investigation in clinical_data["investigations"]:
                    self.db_service.add_investigation(investigation)
                    counts["investigations"] += 1

                for procedure in clinical_data["procedures"]:
                    self.db_service.add_procedure(procedure)
                    counts["procedures"] += 1

        logger.info(f"Seeding completed: {counts}")
        return counts


def seed_database(db_service) -> dict:
    """Seed the database with sample data if it's empty.

    Args:
        db_service: DatabaseService instance

    Returns:
        Dictionary with counts of created records, or None if database already had data
    """
    # Check if database already has patients
    existing_patients = db_service.get_all_patients()

    if existing_patients:
        logger.info(f"Database already has {len(existing_patients)} patients. Skipping seeding.")
        return None

    logger.info("Database is empty. Starting sample data seeding...")
    seeder = SampleDataSeeder(db_service)
    counts = seeder.seed()

    logger.info(f"Successfully seeded database with:")
    logger.info(f"  - {counts['patients']} patients")
    logger.info(f"  - {counts['visits']} visits")
    logger.info(f"  - {counts['investigations']} investigations")
    logger.info(f"  - {counts['procedures']} procedures")

    return counts
