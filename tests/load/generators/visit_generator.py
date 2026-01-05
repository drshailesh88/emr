"""Generate realistic visit data for load testing."""

import random
from datetime import datetime, timedelta, date
from typing import List, Optional

# Common chief complaints by specialty/system
CHIEF_COMPLAINTS = {
    'general': [
        'Fever since 3 days',
        'Body ache and weakness',
        'Headache',
        'Fatigue and tiredness',
        'Weight loss',
        'Loss of appetite',
        'Dizziness',
        'General weakness'
    ],
    'respiratory': [
        'Cough and cold',
        'Breathlessness',
        'Chest pain',
        'Difficulty breathing',
        'Wheezing',
        'Sore throat',
        'Runny nose',
        'Productive cough with sputum'
    ],
    'cardiovascular': [
        'Chest pain on exertion',
        'Palpitations',
        'Swelling in legs',
        'Chest discomfort',
        'Irregular heartbeat',
        'High BP complaints'
    ],
    'gastrointestinal': [
        'Abdominal pain',
        'Loose motions',
        'Constipation',
        'Acidity and heartburn',
        'Vomiting',
        'Nausea',
        'Loss of appetite',
        'Stomach upset'
    ],
    'musculoskeletal': [
        'Joint pain',
        'Back pain',
        'Knee pain',
        'Neck pain',
        'Muscle ache',
        'Pain in lower back',
        'Stiffness in joints'
    ],
    'endocrine': [
        'Excessive thirst',
        'Frequent urination',
        'Increased hunger',
        'Weight gain',
        'Heat or cold intolerance',
        'Fatigue'
    ],
    'follow_up': [
        'Follow up for diabetes',
        'Follow up for hypertension',
        'Routine check-up',
        'Review reports',
        'Medication refill'
    ]
}

# Clinical notes templates
CLINICAL_NOTES_TEMPLATES = [
    "Patient presents with {complaint}. Started {duration} ago. {severity}. No associated symptoms. Vitals stable. {examination}",
    "{complaint} for {duration}. {severity}. On examination: {examination}. Patient alert and oriented.",
    "c/o {complaint} x {duration}. {severity}. O/E: {examination}. Advised investigations and treatment.",
    "Patient complains of {complaint}. Duration: {duration}. {examination}. Rest of systemic examination normal.",
]

SEVERITY_DESCRIPTORS = [
    'Mild discomfort',
    'Moderate severity',
    'Significant discomfort',
    'Gradually worsening',
    'Intermittent',
    'Constant',
    'Better with rest',
    'Worse at night'
]

EXAMINATION_FINDINGS = [
    'No significant abnormality detected',
    'Chest clear, cardiovascular system normal',
    'Mild tenderness noted',
    'BP: 130/80, Pulse: 78/min regular',
    'Afebrile, well hydrated',
    'Respiratory rate normal, SpO2 98% on room air',
    'Abdomen soft, non-tender',
    'No pallor, icterus, cyanosis, clubbing, lymphadenopathy'
]

# Common diagnoses
DIAGNOSES = {
    'general': [
        'Viral Fever',
        'Upper Respiratory Tract Infection',
        'Acute Gastroenteritis',
        'Migraine',
        'Tension Headache',
        'Viral illness'
    ],
    'chronic': [
        'Type 2 Diabetes Mellitus',
        'Essential Hypertension',
        'Dyslipidemia',
        'Hypothyroidism',
        'Osteoarthritis',
        'GERD',
        'Chronic Kidney Disease - Stage 3'
    ],
    'respiratory': [
        'Acute Bronchitis',
        'Pneumonia',
        'Asthma',
        'COPD',
        'Allergic Rhinitis',
        'Pharyngitis'
    ],
    'cardiovascular': [
        'Stable Angina',
        'Atrial Fibrillation',
        'Congestive Heart Failure',
        'Coronary Artery Disease'
    ]
}


def generate_visit(
    patient_id: int,
    visit_date: Optional[date] = None,
    visit_type: str = 'general'
) -> dict:
    """Generate a single realistic visit.

    Args:
        patient_id: ID of the patient
        visit_date: Date of visit (defaults to random recent date)
        visit_type: Type of visit ('general', 'chronic', 'respiratory', etc.)

    Returns:
        Dict with visit data
    """
    if visit_date is None:
        # Random date in last 2 years
        days_ago = random.randint(0, 730)
        visit_date = date.today() - timedelta(days=days_ago)

    # Select chief complaint based on visit type
    if visit_type in CHIEF_COMPLAINTS:
        complaint = random.choice(CHIEF_COMPLAINTS[visit_type])
    else:
        # Random from any category
        all_complaints = []
        for category in CHIEF_COMPLAINTS.values():
            all_complaints.extend(category)
        complaint = random.choice(all_complaints)

    # Generate clinical notes
    template = random.choice(CLINICAL_NOTES_TEMPLATES)
    duration = random.choice(['1 day', '2 days', '3 days', '1 week', '2 weeks'])
    severity = random.choice(SEVERITY_DESCRIPTORS)
    examination = random.choice(EXAMINATION_FINDINGS)

    clinical_notes = template.format(
        complaint=complaint.lower(),
        duration=duration,
        severity=severity,
        examination=examination
    )

    # Select diagnosis based on visit type
    if visit_type in DIAGNOSES:
        diagnosis = random.choice(DIAGNOSES[visit_type])
    else:
        # Random from general diagnoses
        diagnosis = random.choice(DIAGNOSES['general'])

    return {
        'patient_id': patient_id,
        'visit_date': visit_date,
        'chief_complaint': complaint,
        'clinical_notes': clinical_notes,
        'diagnosis': diagnosis,
        'prescription_json': None  # Will be filled by prescription generator
    }


def generate_patient_visits(
    patient_id: int,
    visit_count: int,
    start_date: Optional[date] = None,
    chronic_condition: Optional[str] = None
) -> List[dict]:
    """Generate multiple visits for a single patient.

    Args:
        patient_id: ID of the patient
        visit_count: Number of visits to generate
        start_date: First visit date (defaults to 2 years ago)
        chronic_condition: If set, includes regular follow-ups

    Returns:
        List of visit dicts
    """
    if start_date is None:
        start_date = date.today() - timedelta(days=730)

    visits = []

    if chronic_condition:
        # For chronic patients, mix follow-ups with acute visits
        for i in range(visit_count):
            # Chronic patients visit every 1-3 months
            days_between = random.randint(30, 90)
            visit_date = start_date + timedelta(days=i * days_between)

            if visit_date > date.today():
                break

            # 70% follow-ups, 30% acute visits
            if random.random() < 0.7:
                visit = generate_visit(patient_id, visit_date, 'follow_up')
                visit['diagnosis'] = chronic_condition
            else:
                visit = generate_visit(patient_id, visit_date, 'general')

            visits.append(visit)
    else:
        # For non-chronic patients, random acute visits
        for i in range(visit_count):
            # Random gaps between visits (weeks to months)
            if i == 0:
                visit_date = start_date
            else:
                days_gap = random.randint(7, 180)
                visit_date = visits[-1]['visit_date'] + timedelta(days=days_gap)

            if visit_date > date.today():
                break

            visit_type = random.choice(['general', 'respiratory', 'gastrointestinal',
                                       'musculoskeletal'])
            visit = generate_visit(patient_id, visit_date, visit_type)
            visits.append(visit)

    return visits


def generate_heavy_patient_visits(patient_id: int) -> List[dict]:
    """Generate a large number of visits for stress testing.

    Creates 50-100 visits spanning 5 years with realistic spacing.

    Args:
        patient_id: ID of the patient

    Returns:
        List of visit dicts
    """
    visit_count = random.randint(50, 100)
    start_date = date.today() - timedelta(days=1825)  # 5 years ago

    # Heavy patients have chronic conditions
    chronic_condition = random.choice([
        'Type 2 Diabetes Mellitus, Essential Hypertension',
        'Coronary Artery Disease, Dyslipidemia',
        'Chronic Kidney Disease - Stage 3, Hypertension',
        'COPD, Ischemic Heart Disease'
    ])

    return generate_patient_visits(
        patient_id,
        visit_count,
        start_date,
        chronic_condition
    )


def generate_recent_visits(patient_id: int, days: int = 30) -> List[dict]:
    """Generate visits within recent time period.

    Args:
        patient_id: ID of the patient
        days: Number of days to look back

    Returns:
        List of recent visit dicts
    """
    visit_count = random.randint(1, 3)
    start_date = date.today() - timedelta(days=days)

    visits = []
    for i in range(visit_count):
        days_ago = random.randint(0, days)
        visit_date = date.today() - timedelta(days=days_ago)
        visit = generate_visit(patient_id, visit_date)
        visits.append(visit)

    return visits


def generate_visit_sequence(
    patient_id: int,
    condition: str,
    visit_count: int = 5
) -> List[dict]:
    """Generate a sequence of related visits showing disease progression.

    Args:
        patient_id: ID of the patient
        condition: Medical condition being followed
        visit_count: Number of visits in sequence

    Returns:
        List of visit dicts showing progression
    """
    visits = []
    start_date = date.today() - timedelta(days=180)

    progression_templates = {
        'Diabetes': [
            ('Newly diagnosed diabetes', 'Type 2 Diabetes Mellitus'),
            ('Follow up - sugar control', 'Type 2 Diabetes Mellitus - improving'),
            ('Follow up - HbA1c check', 'Type 2 Diabetes Mellitus - controlled'),
            ('Routine diabetic follow up', 'Type 2 Diabetes Mellitus - well controlled'),
            ('Annual diabetic review', 'Type 2 Diabetes Mellitus - stable')
        ],
        'Hypertension': [
            ('High BP detected', 'Essential Hypertension - Grade 1'),
            ('Follow up - BP check', 'Essential Hypertension - improving'),
            ('Medication review', 'Essential Hypertension - controlled'),
            ('Routine BP check', 'Essential Hypertension - well controlled'),
            ('Follow up', 'Essential Hypertension - stable')
        ]
    }

    templates = progression_templates.get(condition, [
        ('Initial visit', condition),
        ('Follow up', condition),
        ('Review', condition),
        ('Routine check', condition),
        ('Follow up', condition)
    ])

    for i in range(min(visit_count, len(templates))):
        # Visits every 30-45 days
        visit_date = start_date + timedelta(days=i * random.randint(30, 45))

        complaint, diagnosis = templates[i]

        visit = {
            'patient_id': patient_id,
            'visit_date': visit_date,
            'chief_complaint': complaint,
            'clinical_notes': f"Patient for {complaint.lower()}. {random.choice(EXAMINATION_FINDINGS)}",
            'diagnosis': diagnosis,
            'prescription_json': None
        }
        visits.append(visit)

    return visits


if __name__ == '__main__':
    # Test the generator
    print("Testing visit generator...")

    # Single visit
    visit = generate_visit(1)
    print(f"\nSingle visit:")
    print(f"  Date: {visit['visit_date']}")
    print(f"  Complaint: {visit['chief_complaint']}")
    print(f"  Diagnosis: {visit['diagnosis']}")

    # Multiple visits for chronic patient
    print("\nChronic patient visits:")
    visits = generate_patient_visits(1, 5, chronic_condition='Type 2 Diabetes Mellitus')
    for v in visits:
        print(f"  {v['visit_date']}: {v['chief_complaint']}")

    # Heavy patient
    print("\nHeavy patient visits:")
    heavy_visits = generate_heavy_patient_visits(1)
    print(f"  Generated {len(heavy_visits)} visits")
    print(f"  Date range: {heavy_visits[0]['visit_date']} to {heavy_visits[-1]['visit_date']}")
