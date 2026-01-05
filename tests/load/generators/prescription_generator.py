"""Generate realistic prescription data for load testing."""

import json
import random
from typing import List, Optional

# Common drugs by category
DRUG_DATABASE = {
    'diabetes': [
        {'name': 'Metformin', 'strengths': ['500mg', '850mg', '1000mg'], 'form': 'tablet'},
        {'name': 'Glimepiride', 'strengths': ['1mg', '2mg', '4mg'], 'form': 'tablet'},
        {'name': 'Sitagliptin', 'strengths': ['50mg', '100mg'], 'form': 'tablet'},
        {'name': 'Empagliflozin', 'strengths': ['10mg', '25mg'], 'form': 'tablet'},
        {'name': 'Insulin Glargine', 'strengths': ['100IU/ml'], 'form': 'injection'},
    ],
    'hypertension': [
        {'name': 'Amlodipine', 'strengths': ['5mg', '10mg'], 'form': 'tablet'},
        {'name': 'Telmisartan', 'strengths': ['40mg', '80mg'], 'form': 'tablet'},
        {'name': 'Atenolol', 'strengths': ['25mg', '50mg', '100mg'], 'form': 'tablet'},
        {'name': 'Enalapril', 'strengths': ['2.5mg', '5mg', '10mg'], 'form': 'tablet'},
        {'name': 'Hydrochlorothiazide', 'strengths': ['12.5mg', '25mg'], 'form': 'tablet'},
    ],
    'dyslipidemia': [
        {'name': 'Atorvastatin', 'strengths': ['10mg', '20mg', '40mg'], 'form': 'tablet'},
        {'name': 'Rosuvastatin', 'strengths': ['5mg', '10mg', '20mg'], 'form': 'tablet'},
        {'name': 'Fenofibrate', 'strengths': ['145mg', '160mg'], 'form': 'tablet'},
    ],
    'antibiotics': [
        {'name': 'Amoxicillin', 'strengths': ['250mg', '500mg'], 'form': 'capsule'},
        {'name': 'Azithromycin', 'strengths': ['250mg', '500mg'], 'form': 'tablet'},
        {'name': 'Ciprofloxacin', 'strengths': ['250mg', '500mg'], 'form': 'tablet'},
        {'name': 'Cefixime', 'strengths': ['200mg', '400mg'], 'form': 'tablet'},
    ],
    'analgesics': [
        {'name': 'Paracetamol', 'strengths': ['500mg', '650mg'], 'form': 'tablet'},
        {'name': 'Ibuprofen', 'strengths': ['200mg', '400mg'], 'form': 'tablet'},
        {'name': 'Diclofenac', 'strengths': ['50mg', '75mg'], 'form': 'tablet'},
        {'name': 'Tramadol', 'strengths': ['50mg', '100mg'], 'form': 'tablet'},
    ],
    'gastro': [
        {'name': 'Pantoprazole', 'strengths': ['20mg', '40mg'], 'form': 'tablet'},
        {'name': 'Rabeprazole', 'strengths': ['20mg'], 'form': 'tablet'},
        {'name': 'Domperidone', 'strengths': ['10mg'], 'form': 'tablet'},
        {'name': 'Ondansetron', 'strengths': ['4mg', '8mg'], 'form': 'tablet'},
    ],
    'respiratory': [
        {'name': 'Salbutamol', 'strengths': ['2mg', '4mg'], 'form': 'tablet'},
        {'name': 'Montelukast', 'strengths': ['10mg'], 'form': 'tablet'},
        {'name': 'Cetirizine', 'strengths': ['5mg', '10mg'], 'form': 'tablet'},
        {'name': 'Levosalbutamol', 'strengths': ['1mg'], 'form': 'respules'},
    ],
    'thyroid': [
        {'name': 'Levothyroxine', 'strengths': ['25mcg', '50mcg', '75mcg', '100mcg'], 'form': 'tablet'},
    ],
    'supplements': [
        {'name': 'Vitamin D3', 'strengths': ['60000IU'], 'form': 'sachet'},
        {'name': 'Calcium', 'strengths': ['500mg'], 'form': 'tablet'},
        {'name': 'Vitamin B12', 'strengths': ['1000mcg'], 'form': 'tablet'},
        {'name': 'Folic Acid', 'strengths': ['5mg'], 'form': 'tablet'},
    ]
}

FREQUENCIES = ['OD', 'BD', 'TDS', 'QID', 'HS', 'SOS']
DURATIONS = ['3 days', '5 days', '7 days', '10 days', '14 days', '1 month', '2 months', '3 months']
INSTRUCTIONS = [
    'after meals',
    'before meals',
    'empty stomach',
    'with water',
    'at bedtime',
    'morning and evening',
    'as directed',
    'when required'
]

# Common investigations by condition
INVESTIGATIONS = {
    'diabetes': ['FBS', 'PPBS', 'HbA1c', 'Lipid Profile', 'Kidney Function Test', 'Urine Routine'],
    'hypertension': ['ECG', 'Echocardiography', 'Lipid Profile', 'Kidney Function Test', 'Urine Routine'],
    'general': ['CBC', 'ESR', 'CRP', 'Urine Routine', 'Chest X-ray'],
    'thyroid': ['TSH', 'T3', 'T4', 'Free T3', 'Free T4'],
    'cardiac': ['ECG', 'Echo', 'TMT', 'Lipid Profile', 'Troponin'],
    'infection': ['CBC', 'ESR', 'CRP', 'Blood Culture', 'Urine Culture'],
}

ADVICE = {
    'diabetes': [
        'Diet control - avoid sugar and refined carbs',
        'Regular exercise - 30 min walking daily',
        'Monitor blood sugar regularly',
        'Avoid smoking and alcohol',
        'Maintain healthy weight'
    ],
    'hypertension': [
        'Low salt diet',
        'Regular exercise',
        'Monitor BP daily',
        'Avoid stress',
        'Weight reduction if overweight'
    ],
    'general': [
        'Adequate rest',
        'Plenty of fluids',
        'Balanced diet',
        'Regular exercise',
        'Follow up if symptoms persist'
    ]
}


def generate_medication(category: str = None) -> dict:
    """Generate a single medication entry.

    Args:
        category: Drug category (diabetes, hypertension, etc.) or None for random

    Returns:
        Dict with medication details
    """
    if category is None or category not in DRUG_DATABASE:
        category = random.choice(list(DRUG_DATABASE.keys()))

    drug_info = random.choice(DRUG_DATABASE[category])

    return {
        'drug_name': drug_info['name'],
        'strength': random.choice(drug_info['strengths']),
        'form': drug_info['form'],
        'dose': '1',
        'frequency': random.choice(FREQUENCIES),
        'duration': random.choice(DURATIONS),
        'instructions': random.choice(INSTRUCTIONS)
    }


def generate_prescription(
    diagnosis: str,
    medication_count: Optional[int] = None,
    include_investigations: bool = True,
    include_advice: bool = True
) -> dict:
    """Generate a complete prescription JSON.

    Args:
        diagnosis: Primary diagnosis
        medication_count: Number of medications (random 1-5 if None)
        include_investigations: Whether to include investigations
        include_advice: Whether to include advice

    Returns:
        Dict matching prescription JSON schema
    """
    if medication_count is None:
        medication_count = random.randint(1, 5)

    # Determine drug categories based on diagnosis
    diagnosis_lower = diagnosis.lower()
    categories = []

    if 'diabetes' in diagnosis_lower:
        categories.extend(['diabetes'] * 2)
    if 'hypertension' in diagnosis_lower or 'bp' in diagnosis_lower:
        categories.extend(['hypertension'] * 2)
    if 'dyslipidemia' in diagnosis_lower or 'cholesterol' in diagnosis_lower:
        categories.append('dyslipidemia')
    if 'thyroid' in diagnosis_lower:
        categories.append('thyroid')

    # Always include general categories
    categories.extend(['analgesics', 'gastro', 'supplements'])

    # Generate medications
    medications = []
    used_drugs = set()

    for _ in range(medication_count):
        if categories:
            category = random.choice(categories)
        else:
            category = random.choice(list(DRUG_DATABASE.keys()))

        # Avoid duplicate drugs
        for _ in range(10):  # Max 10 attempts to find unique drug
            med = generate_medication(category)
            if med['drug_name'] not in used_drugs:
                medications.append(med)
                used_drugs.add(med['drug_name'])
                break

    # Generate investigations
    investigations = []
    if include_investigations:
        if 'diabetes' in diagnosis_lower:
            inv_category = 'diabetes'
        elif 'hypertension' in diagnosis_lower:
            inv_category = 'hypertension'
        elif 'thyroid' in diagnosis_lower:
            inv_category = 'thyroid'
        elif 'cardiac' in diagnosis_lower or 'heart' in diagnosis_lower:
            inv_category = 'cardiac'
        else:
            inv_category = 'general'

        inv_list = INVESTIGATIONS.get(inv_category, INVESTIGATIONS['general'])
        investigations = random.sample(inv_list, k=min(3, len(inv_list)))

    # Generate advice
    advice = []
    if include_advice:
        if 'diabetes' in diagnosis_lower:
            advice_category = 'diabetes'
        elif 'hypertension' in diagnosis_lower:
            advice_category = 'hypertension'
        else:
            advice_category = 'general'

        advice_list = ADVICE.get(advice_category, ADVICE['general'])
        advice = random.sample(advice_list, k=min(3, len(advice_list)))

    # Follow-up period
    follow_up_options = ['3 days', '1 week', '2 weeks', '1 month', '2 months', '3 months']
    follow_up = random.choice(follow_up_options)

    # Red flags
    red_flags = []
    if random.random() < 0.3:  # 30% chance of red flags
        common_red_flags = [
            'Chest pain or breathlessness',
            'Severe headache',
            'High fever > 102°F',
            'Persistent vomiting',
            'Severe abdominal pain',
            'Confusion or altered sensorium'
        ]
        red_flags = random.sample(common_red_flags, k=random.randint(1, 2))

    prescription = {
        'diagnosis': [diagnosis],
        'medications': medications,
        'investigations': investigations,
        'advice': advice,
        'follow_up': follow_up,
        'red_flags': red_flags
    }

    return prescription


def generate_prescription_json(diagnosis: str, **kwargs) -> str:
    """Generate prescription as JSON string.

    Args:
        diagnosis: Primary diagnosis
        **kwargs: Additional arguments passed to generate_prescription

    Returns:
        JSON string of prescription
    """
    prescription = generate_prescription(diagnosis, **kwargs)
    return json.dumps(prescription, indent=2)


def generate_chronic_prescription(condition: str) -> dict:
    """Generate prescription for chronic condition follow-up.

    Args:
        condition: Chronic condition (diabetes, hypertension, etc.)

    Returns:
        Prescription dict with chronic medications
    """
    condition_lower = condition.lower()

    # Chronic prescriptions have more medications
    medication_count = random.randint(3, 6)

    # Chronic prescriptions have longer durations
    DURATIONS_CHRONIC = ['1 month', '2 months', '3 months']

    medications = []

    if 'diabetes' in condition_lower:
        # Add diabetes medications
        for drug in random.sample(DRUG_DATABASE['diabetes'], k=min(2, len(DRUG_DATABASE['diabetes']))):
            med = {
                'drug_name': drug['name'],
                'strength': random.choice(drug['strengths']),
                'form': drug['form'],
                'dose': '1',
                'frequency': random.choice(['OD', 'BD']),
                'duration': random.choice(DURATIONS_CHRONIC),
                'instructions': random.choice(['before meals', 'after meals'])
            }
            medications.append(med)

    if 'hypertension' in condition_lower or 'bp' in condition_lower:
        # Add BP medications
        for drug in random.sample(DRUG_DATABASE['hypertension'], k=min(2, len(DRUG_DATABASE['hypertension']))):
            med = {
                'drug_name': drug['name'],
                'strength': random.choice(drug['strengths']),
                'form': drug['form'],
                'dose': '1',
                'frequency': 'OD',
                'duration': random.choice(DURATIONS_CHRONIC),
                'instructions': random.choice(['morning', 'evening', 'after meals'])
            }
            medications.append(med)

    # Add statin if multiple conditions
    if random.random() < 0.5:
        statin = random.choice(DRUG_DATABASE['dyslipidemia'])
        medications.append({
            'drug_name': statin['name'],
            'strength': random.choice(statin['strengths']),
            'form': statin['form'],
            'dose': '1',
            'frequency': 'HS',
            'duration': random.choice(DURATIONS_CHRONIC),
            'instructions': 'at bedtime'
        })

    # Pad with supplements if needed
    while len(medications) < medication_count:
        supp = random.choice(DRUG_DATABASE['supplements'])
        medications.append({
            'drug_name': supp['name'],
            'strength': random.choice(supp['strengths']),
            'form': supp['form'],
            'dose': '1',
            'frequency': random.choice(['OD', 'Once weekly']),
            'duration': random.choice(DURATIONS_CHRONIC),
            'instructions': random.choice(INSTRUCTIONS)
        })

    prescription = {
        'diagnosis': [condition],
        'medications': medications,
        'investigations': [],
        'advice': ADVICE.get('diabetes' if 'diabetes' in condition_lower else 'hypertension', ADVICE['general']),
        'follow_up': random.choice(['1 month', '2 months', '3 months']),
        'red_flags': []
    }

    return prescription


if __name__ == '__main__':
    # Test the generator
    print("Testing prescription generator...")

    # Simple prescription
    rx = generate_prescription('Viral Fever', medication_count=3)
    print(f"\nViral Fever Prescription:")
    print(f"  Medications: {len(rx['medications'])}")
    for med in rx['medications']:
        print(f"    - {med['drug_name']} {med['strength']} {med['frequency']}")

    # Chronic prescription
    chronic_rx = generate_chronic_prescription('Type 2 Diabetes Mellitus, Hypertension')
    print(f"\nChronic Prescription:")
    print(f"  Medications: {len(chronic_rx['medications'])}")
    for med in chronic_rx['medications']:
        print(f"    - {med['drug_name']} {med['strength']} for {med['duration']}")

    # JSON output
    print("\nJSON Prescription:")
    print(generate_prescription_json('Acute Gastroenteritis', medication_count=2))
