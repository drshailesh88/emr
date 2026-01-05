"""Red flag medical emergency scenario fixtures for DocAssist EMR testing."""

from typing import Dict, List
from datetime import date


# ============== RED FLAG SCENARIOS ==============

RED_FLAG_SCENARIOS = {
    # Cardiac emergencies
    'acute_mi': {
        'symptoms': [
            'Severe central chest pain',
            'Pain radiating to left arm and jaw',
            'Profuse sweating',
            'Nausea and vomiting',
            'Anxiety and sense of impending doom'
        ],
        'vitals': {
            'BP': '90/60',
            'HR': '110',
            'SpO2': '94%',
            'RR': '22'
        },
        'duration': '2 hours',
        'risk_factors': ['Age 60', 'Male', 'Smoker', 'Hypertension', 'Family history CAD'],
        'expected_flags': [
            'Possible Acute Coronary Syndrome - STEMI',
            'Hypotension',
            'Tachycardia'
        ],
        'expected_urgency': 'EMERGENCY',
        'expected_action': 'IMMEDIATE HOSPITALIZATION',
        'immediate_management': [
            'MONA protocol: Morphine, Oxygen, Nitrates, Aspirin',
            'Aspirin 325mg STAT (chew)',
            'Clopidogrel 600mg loading dose',
            'Urgent ECG',
            'Troponin I/T',
            'Transfer to cath lab for primary PCI'
        ],
        'time_sensitive': 'Door to balloon <90 minutes',
        'differential_diagnosis': ['STEMI', 'NSTEMI', 'Unstable angina', 'Aortic dissection']
    },

    'acute_heart_failure': {
        'symptoms': [
            'Severe breathlessness at rest',
            'Cannot lie flat (orthopnea)',
            'Pink frothy sputum',
            'Bilateral leg swelling'
        ],
        'vitals': {
            'BP': '180/110',
            'HR': '130',
            'SpO2': '85%',
            'RR': '32'
        },
        'duration': '6 hours, worsening',
        'risk_factors': ['Known heart failure', 'Missed diuretic doses'],
        'expected_flags': [
            'Acute Decompensated Heart Failure',
            'Severe hypertension',
            'Hypoxia',
            'Tachypnea'
        ],
        'expected_urgency': 'EMERGENCY',
        'expected_action': 'IMMEDIATE HOSPITALIZATION',
        'immediate_management': [
            'Sit patient upright',
            '100% oxygen',
            'IV furosemide 40mg STAT',
            'Nitroglycerin sublingual',
            'Monitor oxygen saturation',
            'ICU admission'
        ],
        'differential_diagnosis': ['Acute pulmonary edema', 'Pneumonia', 'Pulmonary embolism']
    },

    # Neurological emergencies
    'stroke': {
        'symptoms': [
            'Sudden onset right-sided weakness',
            'Facial droop (right side)',
            'Slurred speech',
            'Unable to lift right arm'
        ],
        'vitals': {
            'BP': '185/105',
            'HR': '88',
            'SpO2': '97%',
            'Blood sugar': '145'
        },
        'duration': '1 hour ago',
        'risk_factors': ['Age 68', 'Hypertension', 'Atrial fibrillation', 'Not on anticoagulation'],
        'expected_flags': [
            'Acute Stroke - likely ischemic',
            'Hypertension',
            'FAST positive (Face, Arm, Speech, Time)'
        ],
        'expected_urgency': 'EMERGENCY',
        'expected_action': 'IMMEDIATE HOSPITALIZATION - Stroke Code',
        'immediate_management': [
            'Urgent non-contrast CT head',
            'Check blood sugar',
            'Do NOT lower BP acutely (unless >220/120)',
            'Consider thrombolysis if within 4.5 hours',
            'Stroke unit admission',
            'Aspirin 300mg (after ruling out hemorrhage)'
        ],
        'time_sensitive': 'Time is brain - thrombolysis window 4.5 hours',
        'differential_diagnosis': ['Ischemic stroke', 'Hemorrhagic stroke', 'TIA', 'Todd paresis']
    },

    'meningitis': {
        'symptoms': [
            'Severe headache (worst headache of life)',
            'Fever 103°F',
            'Neck stiffness',
            'Photophobia',
            'Altered mental status',
            'Vomiting'
        ],
        'vitals': {
            'BP': '95/60',
            'HR': '125',
            'Temperature': '103°F',
            'RR': '28'
        },
        'duration': '8 hours',
        'risk_factors': ['Recent upper respiratory infection'],
        'expected_flags': [
            'Possible bacterial meningitis',
            'Hypotension',
            'Fever',
            'Tachycardia',
            'Meningeal signs positive'
        ],
        'expected_urgency': 'EMERGENCY',
        'expected_action': 'IMMEDIATE HOSPITALIZATION',
        'immediate_management': [
            'Blood cultures BEFORE antibiotics',
            'Empiric antibiotics STAT (Ceftriaxone 2g IV)',
            'Dexamethasone 10mg IV before/with first antibiotic dose',
            'Lumbar puncture (if no contraindications)',
            'IV fluids',
            'ICU admission'
        ],
        'time_sensitive': 'Antibiotics within 1 hour',
        'differential_diagnosis': ['Bacterial meningitis', 'Viral meningitis', 'Subarachnoid hemorrhage']
    },

    'subarachnoid_hemorrhage': {
        'symptoms': [
            'Thunderclap headache (sudden, severe)',
            'Worst headache of life',
            'Neck stiffness',
            'Photophobia',
            'Vomiting',
            'Brief loss of consciousness'
        ],
        'vitals': {
            'BP': '170/95',
            'HR': '88',
            'SpO2': '98%'
        },
        'duration': 'Started 2 hours ago, sudden onset',
        'risk_factors': ['Smoking', 'Hypertension', 'Family history of aneurysm'],
        'expected_flags': [
            'Possible subarachnoid hemorrhage',
            'Thunderclap headache',
            'Hypertension'
        ],
        'expected_urgency': 'EMERGENCY',
        'expected_action': 'IMMEDIATE HOSPITALIZATION',
        'immediate_management': [
            'Urgent non-contrast CT head',
            'If CT negative but high suspicion - lumbar puncture',
            'Neurosurgery consult',
            'Blood pressure control (target SBP 140-160)',
            'Nimodipine to prevent vasospasm',
            'ICU admission'
        ],
        'time_sensitive': 'CT within 6 hours has 95% sensitivity',
        'differential_diagnosis': ['SAH', 'Meningitis', 'Migraine', 'Cerebral venous thrombosis']
    },

    # Respiratory emergencies
    'severe_asthma_attack': {
        'symptoms': [
            'Severe breathlessness',
            'Cannot speak in full sentences',
            'Using accessory muscles',
            'Wheezing',
            'Chest tightness'
        ],
        'vitals': {
            'BP': '130/85',
            'HR': '130',
            'SpO2': '88%',
            'RR': '35',
            'Peak flow': '<50% of best'
        },
        'duration': '4 hours, worsening despite inhaler use',
        'risk_factors': ['Known asthma', 'Previous ICU admissions for asthma'],
        'expected_flags': [
            'Severe asthma exacerbation - life threatening',
            'Hypoxia',
            'Tachypnea',
            'Tachycardia'
        ],
        'expected_urgency': 'EMERGENCY',
        'expected_action': 'IMMEDIATE HOSPITALIZATION',
        'immediate_management': [
            'High flow oxygen (target SpO2 94-98%)',
            'Salbutamol nebulization 2.5-5mg (can repeat)',
            'Ipratropium nebulization 500mcg',
            'Hydrocortisone 200mg IV or Prednisolone 40mg oral',
            'Magnesium sulphate 2g IV over 20 min',
            'Consider ICU if no improvement'
        ],
        'time_sensitive': 'Can deteriorate rapidly',
        'differential_diagnosis': ['Severe asthma', 'Pneumonia', 'Pneumothorax', 'Pulmonary embolism']
    },

    'pulmonary_embolism': {
        'symptoms': [
            'Sudden onset breathlessness',
            'Chest pain (pleuritic)',
            'Cough with blood-tinged sputum',
            'Leg swelling (unilateral)'
        ],
        'vitals': {
            'BP': '95/60',
            'HR': '125',
            'SpO2': '89%',
            'RR': '28'
        },
        'duration': '2 hours',
        'risk_factors': ['Recent long flight', 'Immobilization', 'Oral contraceptive use'],
        'expected_flags': [
            'Possible pulmonary embolism',
            'Hypotension',
            'Hypoxia',
            'Tachycardia'
        ],
        'expected_urgency': 'EMERGENCY',
        'expected_action': 'IMMEDIATE HOSPITALIZATION',
        'immediate_management': [
            'Oxygen',
            'D-dimer (if low probability)',
            'CT pulmonary angiography',
            'ECG (look for S1Q3T3)',
            'Anticoagulation - LMWH or fondaparinux STAT',
            'Thrombolysis if massive PE with shock'
        ],
        'time_sensitive': 'Can be rapidly fatal',
        'differential_diagnosis': ['PE', 'Pneumonia', 'MI', 'Pneumothorax']
    },

    # Abdominal emergencies
    'ectopic_pregnancy': {
        'symptoms': [
            'Severe lower abdominal pain',
            'Vaginal bleeding (light)',
            'Shoulder tip pain',
            'Dizziness',
            'Syncope'
        ],
        'vitals': {
            'BP': '85/55',
            'HR': '120',
            'SpO2': '96%',
            'Temperature': '98.6°F'
        },
        'duration': 'Pain started 6 hours ago, worsening',
        'risk_factors': ['6 weeks pregnant', 'Previous ectopic', 'PID history'],
        'expected_flags': [
            'Ruptured ectopic pregnancy - hemorrhagic shock',
            'Severe hypotension',
            'Tachycardia',
            'Peritoneal signs'
        ],
        'expected_urgency': 'EMERGENCY',
        'expected_action': 'IMMEDIATE SURGICAL INTERVENTION',
        'immediate_management': [
            'Large bore IV access x 2',
            'IV fluids - crystalloid bolus',
            'Type and crossmatch',
            'Emergency gynecology consult',
            'Urgent ultrasound',
            'Emergency laparotomy',
            'Prepare for blood transfusion'
        ],
        'time_sensitive': 'Life-threatening hemorrhage',
        'differential_diagnosis': ['Ruptured ectopic', 'Ovarian torsion', 'Appendicitis', 'PID']
    },

    'acute_appendicitis': {
        'symptoms': [
            'Periumbilical pain migrating to right lower quadrant',
            'Nausea and vomiting',
            'Fever',
            'Anorexia',
            'Rebound tenderness at McBurney point'
        ],
        'vitals': {
            'BP': '125/80',
            'HR': '105',
            'Temperature': '101.5°F',
            'RR': '20'
        },
        'duration': '12 hours',
        'risk_factors': ['Age 25', 'Male'],
        'expected_flags': [
            'Acute appendicitis',
            'Fever',
            'Tachycardia',
            'Peritoneal signs positive'
        ],
        'expected_urgency': 'URGENT',
        'expected_action': 'SURGICAL CONSULTATION - likely appendectomy',
        'immediate_management': [
            'NPO (nil per oral)',
            'IV fluids',
            'Analgesics',
            'Antibiotics (after surgical decision)',
            'Surgical consult',
            'Ultrasound or CT abdomen'
        ],
        'time_sensitive': 'Risk of perforation after 24-48 hours',
        'differential_diagnosis': ['Appendicitis', 'Mesenteric adenitis', 'UTI', 'Ovarian cyst']
    },

    # Sepsis
    'septic_shock': {
        'symptoms': [
            'High fever with rigors',
            'Altered mental status (confused)',
            'Severe weakness',
            'Rapid breathing',
            'Cold, clammy skin'
        ],
        'vitals': {
            'BP': '75/45',
            'HR': '135',
            'Temperature': '104°F',
            'RR': '32',
            'SpO2': '91%',
            'Urine output': '<30ml/hr'
        },
        'duration': 'Fever for 2 days, deteriorated in last 6 hours',
        'risk_factors': ['Diabetes', 'Recent UTI', 'Immunocompromised'],
        'expected_flags': [
            'Septic shock',
            'Severe hypotension',
            'Fever',
            'Tachycardia',
            'Tachypnea',
            'Altered sensorium',
            'Oliguria'
        ],
        'expected_urgency': 'EMERGENCY',
        'expected_action': 'IMMEDIATE ICU ADMISSION',
        'immediate_management': [
            'Sepsis 6 protocol (within 1 hour):',
            '  1. High flow oxygen',
            '  2. Blood cultures x 2',
            '  3. Broad spectrum antibiotics IV',
            '  4. IV fluids - 30ml/kg crystalloid bolus',
            '  5. Measure lactate',
            '  6. Measure urine output',
            'Vasopressors if BP not responding to fluids',
            'ICU admission'
        ],
        'time_sensitive': 'Each hour delay increases mortality by 7%',
        'differential_diagnosis': ['Septic shock', 'Cardiogenic shock', 'Anaphylaxis']
    },

    # Anaphylaxis
    'anaphylaxis': {
        'symptoms': [
            'Difficulty breathing',
            'Throat tightness',
            'Facial swelling',
            'Urticaria (hives all over body)',
            'Abdominal cramps',
            'Vomiting'
        ],
        'vitals': {
            'BP': '80/50',
            'HR': '130',
            'SpO2': '88%',
            'RR': '28',
            'Stridor': 'present'
        },
        'duration': '15 minutes after bee sting',
        'risk_factors': ['Known allergy to insect venom'],
        'expected_flags': [
            'Anaphylactic shock',
            'Severe hypotension',
            'Hypoxia',
            'Angioedema',
            'Airway compromise'
        ],
        'expected_urgency': 'EMERGENCY',
        'expected_action': 'IMMEDIATE TREATMENT',
        'immediate_management': [
            'Adrenaline 0.5mg IM (1:1000) - anterolateral thigh',
            'Can repeat every 5 minutes if needed',
            'High flow oxygen',
            'IV fluids - rapid bolus',
            'Hydrocortisone 200mg IV',
            'Chlorpheniramine 10mg IV',
            'Nebulized adrenaline if stridor',
            'Prepare for intubation if airway compromise'
        ],
        'time_sensitive': 'Can be fatal within minutes',
        'differential_diagnosis': ['Anaphylaxis', 'Angioedema', 'Asthma', 'Panic attack']
    },

    # DKA
    'diabetic_ketoacidosis': {
        'symptoms': [
            'Polyuria and polydipsia for 2 days',
            'Nausea and vomiting',
            'Abdominal pain',
            'Fruity breath odor',
            'Kussmaul breathing (deep, rapid)',
            'Altered mental status'
        ],
        'vitals': {
            'BP': '95/60',
            'HR': '120',
            'Temperature': '98.6°F',
            'RR': '28',
            'Blood sugar': '450 mg/dL'
        },
        'duration': '2 days',
        'risk_factors': ['Type 1 Diabetes', 'Missed insulin doses', 'Recent infection'],
        'expected_flags': [
            'Diabetic Ketoacidosis',
            'Severe hyperglycemia',
            'Dehydration',
            'Hypotension',
            'Tachycardia'
        ],
        'expected_urgency': 'EMERGENCY',
        'expected_action': 'IMMEDIATE ICU ADMISSION',
        'immediate_management': [
            'IV fluids - 0.9% saline 1L over 1 hour',
            'Insulin infusion - 0.1 unit/kg/hr',
            'Potassium replacement (after checking levels)',
            'ABG - check pH and ketones',
            'Monitor blood sugar hourly',
            'Look for precipitating cause (infection)',
            'ICU admission'
        ],
        'time_sensitive': 'Can progress to coma',
        'differential_diagnosis': ['DKA', 'HHS', 'Lactic acidosis', 'Uremia']
    },
}


# ============== HELPER FUNCTIONS ==============

def get_red_flags_by_urgency(urgency: str) -> Dict:
    """Get all red flag scenarios by urgency level."""
    return {
        name: scenario
        for name, scenario in RED_FLAG_SCENARIOS.items()
        if scenario['expected_urgency'] == urgency
    }


def get_all_red_flag_scenarios() -> Dict:
    """Get all red flag scenarios."""
    return RED_FLAG_SCENARIOS


def get_cardiac_emergencies() -> Dict:
    """Get all cardiac emergency scenarios."""
    return {
        name: scenario
        for name, scenario in RED_FLAG_SCENARIOS.items()
        if any(keyword in name for keyword in ['mi', 'heart', 'cardiac'])
    }


def get_neurological_emergencies() -> Dict:
    """Get all neurological emergency scenarios."""
    return {
        name: scenario
        for name, scenario in RED_FLAG_SCENARIOS.items()
        if any(keyword in name for keyword in ['stroke', 'meningitis', 'hemorrhage'])
    }


def get_respiratory_emergencies() -> Dict:
    """Get all respiratory emergency scenarios."""
    return {
        name: scenario
        for name, scenario in RED_FLAG_SCENARIOS.items()
        if any(keyword in name for keyword in ['asthma', 'embolism', 'respiratory'])
    }


def get_time_sensitive_emergencies() -> Dict:
    """Get all time-sensitive emergencies with specific time windows."""
    return {
        name: scenario
        for name, scenario in RED_FLAG_SCENARIOS.items()
        if 'time_sensitive' in scenario
    }


def get_emergencies_requiring_icu() -> Dict:
    """Get scenarios that require ICU admission."""
    return {
        name: scenario
        for name, scenario in RED_FLAG_SCENARIOS.items()
        if 'ICU' in scenario.get('expected_action', '') or 'ICU' in str(scenario.get('immediate_management', []))
    }


__all__ = [
    "RED_FLAG_SCENARIOS",
    "get_red_flags_by_urgency",
    "get_all_red_flag_scenarios",
    "get_cardiac_emergencies",
    "get_neurological_emergencies",
    "get_respiratory_emergencies",
    "get_time_sensitive_emergencies",
    "get_emergencies_requiring_icu",
]
