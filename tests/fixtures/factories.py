"""Factory functions for generating test data for DocAssist EMR."""

import random
import json
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

from src.models.schemas import (
    Patient, Visit, Prescription, Medication, Investigation,
    Procedure, Vitals, PatientSnapshot
)

from .patients import (
    generate_indian_name, generate_phone_number, generate_address, generate_uhid
)


# ============== FACTORY FUNCTIONS ==============

def create_patient(
    name: Optional[str] = None,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    **overrides
) -> Patient:
    """Create patient with defaults, override as needed.

    Args:
        name: Patient name (generated if not provided)
        age: Patient age (random 25-75 if not provided)
        gender: M/F/O (random if not provided)
        phone: Phone number (generated if not provided)
        address: Address (generated if not provided)
        **overrides: Any other Patient fields to override

    Returns:
        Patient object
    """
    if gender is None:
        gender = random.choice(["M", "F"])

    if name is None:
        name = generate_indian_name(gender)

    if age is None:
        age = random.randint(25, 75)

    if phone is None:
        phone = generate_phone_number()

    if address is None:
        address = generate_address()

    patient_data = {
        "name": name,
        "age": age,
        "gender": gender,
        "phone": phone,
        "address": address,
    }

    # Apply overrides
    patient_data.update(overrides)

    return Patient(**patient_data)


def create_visit(
    patient_id: int,
    visit_date: Optional[date] = None,
    chief_complaint: Optional[str] = None,
    clinical_notes: Optional[str] = None,
    diagnosis: Optional[str] = None,
    prescription: Optional[Prescription] = None,
    **overrides
) -> Visit:
    """Create visit for patient.

    Args:
        patient_id: Patient ID
        visit_date: Date of visit (today if not provided)
        chief_complaint: Chief complaint
        clinical_notes: Clinical notes
        diagnosis: Diagnosis
        prescription: Prescription object (will be serialized to JSON)
        **overrides: Any other Visit fields to override

    Returns:
        Visit object
    """
    if visit_date is None:
        visit_date = date.today()

    if chief_complaint is None:
        chief_complaint = "General checkup"

    if clinical_notes is None:
        clinical_notes = "Patient presents for routine follow-up. No acute complaints."

    if diagnosis is None:
        diagnosis = "Routine follow-up"

    visit_data = {
        "patient_id": patient_id,
        "visit_date": visit_date,
        "chief_complaint": chief_complaint,
        "clinical_notes": clinical_notes,
        "diagnosis": diagnosis,
    }

    # Serialize prescription if provided
    if prescription:
        visit_data["prescription_json"] = json.dumps(prescription.dict())

    # Apply overrides
    visit_data.update(overrides)

    return Visit(**visit_data)


def create_prescription(
    diagnosis: Optional[List[str]] = None,
    medications: Optional[List[Medication]] = None,
    investigations: Optional[List[str]] = None,
    advice: Optional[List[str]] = None,
    follow_up: Optional[str] = None,
    red_flags: Optional[List[str]] = None,
    **overrides
) -> Prescription:
    """Create prescription.

    Args:
        diagnosis: List of diagnoses
        medications: List of Medication objects
        investigations: List of investigation names
        advice: List of advice items
        follow_up: Follow-up instructions
        red_flags: List of red flags
        **overrides: Any other Prescription fields

    Returns:
        Prescription object
    """
    prescription_data = {
        "diagnosis": diagnosis or [],
        "medications": medications or [],
        "investigations": investigations or [],
        "advice": advice or [],
        "follow_up": follow_up or "",
        "red_flags": red_flags or [],
    }

    # Apply overrides
    prescription_data.update(overrides)

    return Prescription(**prescription_data)


def create_medication(
    drug_name: str,
    strength: str = "",
    form: str = "tablet",
    dose: str = "1",
    frequency: str = "OD",
    duration: str = "",
    instructions: str = "",
    **overrides
) -> Medication:
    """Create medication.

    Args:
        drug_name: Name of the drug
        strength: Strength (e.g., "500mg")
        form: Form (tablet, capsule, syrup, etc.)
        dose: Dose (e.g., "1", "2")
        frequency: Frequency (OD, BD, TDS, QID, etc.)
        duration: Duration (e.g., "7 days", "1 month")
        instructions: Special instructions
        **overrides: Any other Medication fields

    Returns:
        Medication object
    """
    med_data = {
        "drug_name": drug_name,
        "strength": strength,
        "form": form,
        "dose": dose,
        "frequency": frequency,
        "duration": duration,
        "instructions": instructions,
    }

    # Apply overrides
    med_data.update(overrides)

    return Medication(**med_data)


def create_investigation(
    patient_id: int,
    test_name: str,
    result: str = "",
    unit: str = "",
    reference_range: str = "",
    test_date: Optional[date] = None,
    is_abnormal: bool = False,
    **overrides
) -> Investigation:
    """Create investigation/lab result.

    Args:
        patient_id: Patient ID
        test_name: Name of the test
        result: Test result
        unit: Unit of measurement
        reference_range: Reference range
        test_date: Date of test (today if not provided)
        is_abnormal: Whether result is abnormal
        **overrides: Any other Investigation fields

    Returns:
        Investigation object
    """
    if test_date is None:
        test_date = date.today()

    investigation_data = {
        "patient_id": patient_id,
        "test_name": test_name,
        "result": result,
        "unit": unit,
        "reference_range": reference_range,
        "test_date": test_date,
        "is_abnormal": is_abnormal,
    }

    # Apply overrides
    investigation_data.update(overrides)

    return Investigation(**investigation_data)


def create_procedure(
    patient_id: int,
    procedure_name: str,
    details: str = "",
    procedure_date: Optional[date] = None,
    notes: str = "",
    **overrides
) -> Procedure:
    """Create procedure record.

    Args:
        patient_id: Patient ID
        procedure_name: Name of the procedure
        details: Procedure details
        procedure_date: Date of procedure (today if not provided)
        notes: Additional notes
        **overrides: Any other Procedure fields

    Returns:
        Procedure object
    """
    if procedure_date is None:
        procedure_date = date.today()

    procedure_data = {
        "patient_id": patient_id,
        "procedure_name": procedure_name,
        "details": details,
        "procedure_date": procedure_date,
        "notes": notes,
    }

    # Apply overrides
    procedure_data.update(overrides)

    return Procedure(**procedure_data)


def create_vitals(
    patient_id: int,
    visit_id: Optional[int] = None,
    bp_systolic: Optional[int] = None,
    bp_diastolic: Optional[int] = None,
    pulse: Optional[int] = None,
    temperature: Optional[float] = None,
    spo2: Optional[int] = None,
    weight: Optional[float] = None,
    **overrides
) -> Vitals:
    """Create vitals record with realistic defaults.

    Args:
        patient_id: Patient ID
        visit_id: Visit ID
        bp_systolic: Systolic BP (120 if not provided)
        bp_diastolic: Diastolic BP (80 if not provided)
        pulse: Pulse rate (75 if not provided)
        temperature: Temperature in F (98.6 if not provided)
        spo2: SpO2 (98 if not provided)
        weight: Weight in kg
        **overrides: Any other Vitals fields

    Returns:
        Vitals object
    """
    vitals_data = {
        "patient_id": patient_id,
        "visit_id": visit_id,
        "bp_systolic": bp_systolic or 120,
        "bp_diastolic": bp_diastolic or 80,
        "pulse": pulse or 75,
        "temperature": temperature or 98.6,
        "spo2": spo2 or 98,
        "weight": weight,
        "recorded_at": datetime.now(),
    }

    # Apply overrides
    vitals_data.update(overrides)

    return Vitals(**vitals_data)


# ============== COMPOSITE DATA GENERATORS ==============

@dataclass
class ClinicData:
    """Container for complete clinic data."""
    patients: List[Patient]
    visits: List[Visit]
    investigations: List[Investigation]
    procedures: List[Procedure]
    vitals: List[Vitals]


def create_clinic_data(
    n_patients: int = 10,
    n_visits_per_patient: int = 5,
    seed: int = 42
) -> ClinicData:
    """Create full clinic with patients, visits, labs.

    Args:
        n_patients: Number of patients to create
        n_visits_per_patient: Average visits per patient
        seed: Random seed for reproducibility

    Returns:
        ClinicData object containing all generated data
    """
    random.seed(seed)

    patients = []
    visits = []
    investigations = []
    procedures = []
    vitals_list = []

    # Create patients
    for i in range(n_patients):
        patient = create_patient()
        patient.id = i + 1
        patient.uhid = generate_uhid(i + 1)
        patients.append(patient)

        # Create visits for this patient
        n_visits = random.randint(
            max(1, n_visits_per_patient - 2),
            n_visits_per_patient + 2
        )

        for v in range(n_visits):
            # Visit date going backwards from today
            visit_date = date.today() - timedelta(days=random.randint(0, 365))

            # Random visit type
            visit_types = [
                "Routine checkup",
                "Follow-up",
                "Fever",
                "Cough and cold",
                "Abdominal pain",
                "Headache",
                "Diabetes checkup"
            ]

            visit = create_visit(
                patient_id=patient.id,
                visit_date=visit_date,
                chief_complaint=random.choice(visit_types),
            )
            visit.id = len(visits) + 1
            visits.append(visit)

            # Create vitals for this visit
            vital = create_vitals(
                patient_id=patient.id,
                visit_id=visit.id,
                bp_systolic=random.randint(110, 140),
                bp_diastolic=random.randint(70, 90),
                pulse=random.randint(65, 90),
                weight=random.uniform(50, 90),
            )
            vital.id = len(vitals_list) + 1
            vitals_list.append(vital)

        # Create some investigations for the patient
        test_names = [
            ("Complete Blood Count", "Normal", "", ""),
            ("Fasting Blood Sugar", str(random.randint(90, 150)), "mg/dL", "70-110"),
            ("HbA1c", f"{random.uniform(5.5, 8.5):.1f}", "%", "<5.7"),
            ("Serum Creatinine", f"{random.uniform(0.8, 1.5):.1f}", "mg/dL", "0.7-1.3"),
        ]

        for test_name, result, unit, ref_range in test_names:
            if random.random() < 0.5:  # 50% chance of having this test
                investigation = create_investigation(
                    patient_id=patient.id,
                    test_name=test_name,
                    result=result,
                    unit=unit,
                    reference_range=ref_range,
                    test_date=date.today() - timedelta(days=random.randint(0, 180)),
                )
                investigation.id = len(investigations) + 1
                investigations.append(investigation)

        # Create some procedures (less common)
        if random.random() < 0.2:  # 20% chance
            procedure_types = [
                "ECG",
                "Chest X-ray",
                "Ultrasound Abdomen",
                "Echocardiography"
            ]

            procedure = create_procedure(
                patient_id=patient.id,
                procedure_name=random.choice(procedure_types),
                details="Routine screening",
                procedure_date=date.today() - timedelta(days=random.randint(0, 180)),
            )
            procedure.id = len(procedures) + 1
            procedures.append(procedure)

    return ClinicData(
        patients=patients,
        visits=visits,
        investigations=investigations,
        procedures=procedures,
        vitals=vitals_list
    )


def create_diabetic_patient_with_history(patient_id: int = 1) -> Dict:
    """Create a complete diabetic patient with full medical history.

    Args:
        patient_id: Patient ID to use

    Returns:
        Dict with patient, visits, investigations, medications
    """
    # Create patient
    patient = create_patient(
        name="Ramesh Kumar",
        age=58,
        gender="M",
        phone="9876543210",
        address="Sector 15, Noida - 201301"
    )
    patient.id = patient_id
    patient.uhid = generate_uhid(patient_id)

    # Create medication history
    medications = [
        create_medication("Metformin", "500mg", dose="1", frequency="BD", instructions="after meals"),
        create_medication("Glimepiride", "2mg", dose="1", frequency="OD", instructions="before breakfast"),
        create_medication("Atorvastatin", "20mg", dose="1", frequency="OD", instructions="at bedtime"),
    ]

    # Create visit history (last 1 year, quarterly visits)
    visits = []
    for i in range(4):
        visit_date = date.today() - timedelta(days=90 * i)

        prescription = create_prescription(
            diagnosis=["Type 2 Diabetes Mellitus", "Dyslipidemia"],
            medications=medications,
            investigations=["HbA1c", "Fasting Lipid Profile", "Kidney Function Test"],
            advice=["Diet control", "Regular exercise", "Monitor blood sugar"],
            follow_up="3 months"
        )

        visit = create_visit(
            patient_id=patient_id,
            visit_date=visit_date,
            chief_complaint="Diabetes follow-up",
            clinical_notes="Routine follow-up. Patient stable. Good compliance.",
            diagnosis="Type 2 Diabetes Mellitus - controlled",
            prescription=prescription
        )
        visits.append(visit)

    # Create investigation history (HbA1c every 3 months)
    investigations = []
    for i in range(4):
        test_date = date.today() - timedelta(days=90 * i)
        hba1c_value = random.uniform(6.5, 7.5)

        investigation = create_investigation(
            patient_id=patient_id,
            test_name="HbA1c",
            result=f"{hba1c_value:.1f}",
            unit="%",
            reference_range="<5.7 (normal), >6.5 (diabetic)",
            test_date=test_date,
            is_abnormal=(hba1c_value > 7.0)
        )
        investigations.append(investigation)

    return {
        "patient": patient,
        "visits": visits,
        "investigations": investigations,
        "medications": medications
    }


def create_emergency_case(emergency_type: str = "chest_pain") -> Dict:
    """Create an emergency case with all relevant data.

    Args:
        emergency_type: Type of emergency (chest_pain, stroke, asthma, etc.)

    Returns:
        Dict with patient and emergency visit
    """
    emergency_templates = {
        "chest_pain": {
            "patient": create_patient(name="Rajiv Mehta", age=60, gender="M"),
            "chief_complaint": "Severe chest pain for 2 hours",
            "diagnosis": "Acute Coronary Syndrome - STEMI",
            "vitals": {
                "bp_systolic": 90,
                "bp_diastolic": 60,
                "pulse": 110,
                "spo2": 94
            }
        },
        "stroke": {
            "patient": create_patient(name="Mohan Patel", age=68, gender="M"),
            "chief_complaint": "Right-sided weakness and speech difficulty",
            "diagnosis": "Acute Ischemic Stroke",
            "vitals": {
                "bp_systolic": 185,
                "bp_diastolic": 105,
                "pulse": 88,
                "spo2": 97
            }
        },
        "asthma": {
            "patient": create_patient(name="Priya Sharma", age=25, gender="F"),
            "chief_complaint": "Severe breathlessness",
            "diagnosis": "Severe Asthma Exacerbation",
            "vitals": {
                "bp_systolic": 130,
                "bp_diastolic": 85,
                "pulse": 130,
                "spo2": 88
            }
        }
    }

    template = emergency_templates.get(emergency_type, emergency_templates["chest_pain"])

    patient = template["patient"]
    patient.id = 1

    visit = create_visit(
        patient_id=1,
        chief_complaint=template["chief_complaint"],
        diagnosis=template["diagnosis"],
        clinical_notes=f"EMERGENCY: {template['chief_complaint']}"
    )

    vitals = create_vitals(
        patient_id=1,
        visit_id=1,
        **template["vitals"]
    )

    return {
        "patient": patient,
        "visit": visit,
        "vitals": vitals
    }


__all__ = [
    "create_patient",
    "create_visit",
    "create_prescription",
    "create_medication",
    "create_investigation",
    "create_procedure",
    "create_vitals",
    "create_clinic_data",
    "create_diabetic_patient_with_history",
    "create_emergency_case",
    "ClinicData",
]
