"""Complete clinic scenarios for DocAssist EMR testing."""

import random
from datetime import date, datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass

from .factories import (
    create_patient, create_visit, create_investigation,
    create_vitals, create_medication, create_prescription
)
from .patients import generate_patients


# ============== CLINIC SCENARIOS ==============

SCENARIOS = {
    'busy_monday_morning': {
        'description': 'Typical busy Monday morning clinic',
        'total_patients': 25,
        'time_period': '9 AM - 1 PM',
        'distribution': {
            'routine_followup': 12,  # 48%
            'new_patients': 5,       # 20%
            'acute_illness': 6,      # 24%
            'emergencies': 2,        # 8%
        },
        'common_complaints': [
            'Diabetes checkup',
            'BP checkup',
            'Fever',
            'Cough and cold',
            'Abdominal pain',
            'Joint pain',
            'Headache',
        ],
        'expected_duration_minutes': 240,
        'avg_consultation_time_minutes': 10,
    },

    'quiet_sunday': {
        'description': 'Quiet Sunday with emergency coverage',
        'total_patients': 8,
        'time_period': '10 AM - 2 PM',
        'distribution': {
            'routine_followup': 3,
            'new_patients': 2,
            'acute_illness': 2,
            'emergencies': 1,
        },
        'common_complaints': [
            'Fever',
            'Injury',
            'Chest pain',
            'Abdominal pain',
        ],
        'expected_duration_minutes': 240,
        'avg_consultation_time_minutes': 15,
    },

    'flu_season': {
        'description': 'Heavy flu season - many respiratory infections',
        'total_patients': 30,
        'time_period': '9 AM - 2 PM',
        'distribution': {
            'routine_followup': 8,
            'new_patients': 4,
            'acute_illness': 16,  # Mostly flu/respiratory
            'emergencies': 2,
        },
        'common_complaints': [
            'Fever with cough',
            'Sore throat',
            'Body ache',
            'Runny nose',
            'Breathlessness',
            'Chest congestion',
        ],
        'expected_duration_minutes': 300,
        'avg_consultation_time_minutes': 10,
    },

    'monsoon_clinic': {
        'description': 'Monsoon season - dengue, malaria, gastroenteritis',
        'total_patients': 28,
        'time_period': '9 AM - 2 PM',
        'distribution': {
            'routine_followup': 10,
            'new_patients': 4,
            'acute_illness': 12,  # Monsoon illnesses
            'emergencies': 2,
        },
        'common_complaints': [
            'High fever',
            'Dengue suspected',
            'Malaria suspected',
            'Diarrhea and vomiting',
            'Typhoid fever',
            'Leptospirosis suspected',
        ],
        'expected_duration_minutes': 300,
        'avg_consultation_time_minutes': 11,
    },

    'diabetes_screening_camp': {
        'description': 'Community diabetes and hypertension screening',
        'total_patients': 50,
        'time_period': '8 AM - 12 PM',
        'distribution': {
            'routine_followup': 0,
            'new_patients': 50,  # All screening
            'acute_illness': 0,
            'emergencies': 0,
        },
        'common_complaints': [
            'Diabetes screening',
            'BP screening',
            'General health checkup',
        ],
        'expected_duration_minutes': 240,
        'avg_consultation_time_minutes': 5,
    },

    'post_holiday_rush': {
        'description': 'Day after Diwali - firework injuries and overeating',
        'total_patients': 35,
        'time_period': '9 AM - 3 PM',
        'distribution': {
            'routine_followup': 8,
            'new_patients': 5,
            'acute_illness': 18,
            'emergencies': 4,
        },
        'common_complaints': [
            'Burn injury (fireworks)',
            'Eye injury',
            'Indigestion',
            'Acidity',
            'Acute gastritis',
            'Asthma exacerbation (smoke)',
        ],
        'expected_duration_minutes': 360,
        'avg_consultation_time_minutes': 10,
    },

    'pediatric_vaccination_day': {
        'description': 'Dedicated pediatric vaccination and checkup day',
        'total_patients': 40,
        'time_period': '10 AM - 2 PM',
        'distribution': {
            'routine_followup': 15,  # Regular pediatric patients
            'new_patients': 20,      # New vaccinations
            'acute_illness': 5,      # Sick children
            'emergencies': 0,
        },
        'common_complaints': [
            'Routine vaccination',
            'Growth monitoring',
            'Fever',
            'Diarrhea',
            'Cough and cold',
        ],
        'expected_duration_minutes': 240,
        'avg_consultation_time_minutes': 6,
    },

    'senior_citizen_clinic': {
        'description': 'Geriatric clinic with polypharmacy patients',
        'total_patients': 20,
        'time_period': '9 AM - 1 PM',
        'distribution': {
            'routine_followup': 15,
            'new_patients': 3,
            'acute_illness': 2,
            'emergencies': 0,
        },
        'common_complaints': [
            'Multiple chronic diseases',
            'Diabetes + Hypertension',
            'Joint pain',
            'Forgetfulness',
            'Insomnia',
            'Constipation',
        ],
        'expected_duration_minutes': 240,
        'avg_consultation_time_minutes': 12,
    },

    'night_emergency_shift': {
        'description': '12-hour night emergency shift',
        'total_patients': 15,
        'time_period': '8 PM - 8 AM',
        'distribution': {
            'routine_followup': 0,
            'new_patients': 3,
            'acute_illness': 8,
            'emergencies': 4,
        },
        'common_complaints': [
            'Chest pain',
            'Breathlessness',
            'Severe abdominal pain',
            'Road traffic accident',
            'High fever',
            'Seizure',
        ],
        'expected_duration_minutes': 720,
        'avg_consultation_time_minutes': 20,
    },

    'antenatal_clinic': {
        'description': 'Dedicated antenatal checkup clinic',
        'total_patients': 25,
        'time_period': '10 AM - 2 PM',
        'distribution': {
            'routine_followup': 20,  # Regular ANC
            'new_patients': 4,       # New pregnancies
            'acute_illness': 1,      # Pregnancy complication
            'emergencies': 0,
        },
        'common_complaints': [
            'Routine antenatal checkup',
            'First trimester visit',
            'Gestational diabetes screening',
            'Pre-eclampsia screening',
            'Fetal movement monitoring',
        ],
        'expected_duration_minutes': 240,
        'avg_consultation_time_minutes': 10,
    },
}


# ============== SCENARIO GENERATORS ==============

@dataclass
class ClinicDay:
    """Complete clinic day data."""
    scenario_name: str
    date: date
    patients: List
    visits: List
    investigations: List
    vitals: List
    statistics: Dict


def generate_clinic_day(
    scenario_name: str,
    clinic_date: date = None,
    seed: int = None
) -> ClinicDay:
    """Generate a complete clinic day based on scenario.

    Args:
        scenario_name: Name of the scenario from SCENARIOS dict
        clinic_date: Date for the clinic (today if not provided)
        seed: Random seed for reproducibility

    Returns:
        ClinicDay object with all data
    """
    if seed:
        random.seed(seed)

    if clinic_date is None:
        clinic_date = date.today()

    scenario = SCENARIOS.get(scenario_name)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_name}")

    patients = []
    visits = []
    investigations = []
    vitals_list = []

    # Generate patients based on distribution
    patient_id = 1

    # Routine follow-ups
    for _ in range(scenario['distribution']['routine_followup']):
        patient = create_patient()
        patient.id = patient_id
        patient.uhid = f"EMR-2024-{patient_id:05d}"
        patients.append(patient)

        # Create follow-up visit
        complaint = random.choice(['Diabetes checkup', 'BP checkup', 'Routine follow-up'])
        visit = create_visit(
            patient_id=patient_id,
            visit_date=clinic_date,
            chief_complaint=complaint,
            diagnosis=f"{complaint} - stable"
        )
        visit.id = patient_id
        visits.append(visit)

        # Add vitals
        vital = create_vitals(
            patient_id=patient_id,
            visit_id=patient_id,
            bp_systolic=random.randint(120, 140),
            bp_diastolic=random.randint(75, 88),
        )
        vitals_list.append(vital)

        patient_id += 1

    # New patients
    for _ in range(scenario['distribution']['new_patients']):
        patient = create_patient()
        patient.id = patient_id
        patient.uhid = f"EMR-2024-{patient_id:05d}"
        patients.append(patient)

        # Create new patient visit
        visit = create_visit(
            patient_id=patient_id,
            visit_date=clinic_date,
            chief_complaint="First visit - general checkup",
            diagnosis="New patient screening"
        )
        visit.id = patient_id
        visits.append(visit)

        # Add vitals and basic investigations
        vital = create_vitals(
            patient_id=patient_id,
            visit_id=patient_id,
        )
        vitals_list.append(vital)

        # Order basic investigations
        investigation = create_investigation(
            patient_id=patient_id,
            test_name="Complete Blood Count",
            result="Pending",
            test_date=clinic_date
        )
        investigations.append(investigation)

        patient_id += 1

    # Acute illness
    for _ in range(scenario['distribution']['acute_illness']):
        patient = create_patient()
        patient.id = patient_id
        patient.uhid = f"EMR-2024-{patient_id:05d}"
        patients.append(patient)

        # Create acute visit
        complaint = random.choice(scenario['common_complaints'])
        visit = create_visit(
            patient_id=patient_id,
            visit_date=clinic_date,
            chief_complaint=complaint,
            diagnosis=f"Acute {complaint}"
        )
        visit.id = patient_id
        visits.append(visit)

        # Add vitals (may be abnormal)
        vital = create_vitals(
            patient_id=patient_id,
            visit_id=patient_id,
            bp_systolic=random.randint(110, 150),
            temperature=random.uniform(98.0, 102.0),
        )
        vitals_list.append(vital)

        patient_id += 1

    # Emergencies
    for _ in range(scenario['distribution']['emergencies']):
        patient = create_patient()
        patient.id = patient_id
        patient.uhid = f"EMR-2024-{patient_id:05d}"
        patients.append(patient)

        # Create emergency visit
        emergency_types = [
            ('Severe chest pain', 'Acute Coronary Syndrome'),
            ('Breathlessness', 'Respiratory distress'),
            ('Severe abdominal pain', 'Acute abdomen'),
            ('High fever with altered sensorium', 'Sepsis'),
        ]
        complaint, diagnosis = random.choice(emergency_types)

        visit = create_visit(
            patient_id=patient_id,
            visit_date=clinic_date,
            chief_complaint=f"EMERGENCY: {complaint}",
            diagnosis=diagnosis
        )
        visit.id = patient_id
        visits.append(visit)

        # Add abnormal vitals
        vital = create_vitals(
            patient_id=patient_id,
            visit_id=patient_id,
            bp_systolic=random.randint(85, 110),  # Hypotensive
            pulse=random.randint(110, 140),       # Tachycardic
            spo2=random.randint(85, 93),          # Hypoxic
        )
        vitals_list.append(vital)

        # Add urgent investigations
        urgent_tests = ['ECG', 'Troponin I', 'CBC', 'ABG']
        for test in urgent_tests[:2]:  # Add 2 urgent tests
            investigation = create_investigation(
                patient_id=patient_id,
                test_name=test,
                result="URGENT - Pending",
                test_date=clinic_date
            )
            investigations.append(investigation)

        patient_id += 1

    # Calculate statistics
    statistics = {
        'total_patients': len(patients),
        'total_visits': len(visits),
        'total_investigations': len(investigations),
        'routine_followup': scenario['distribution']['routine_followup'],
        'new_patients': scenario['distribution']['new_patients'],
        'acute_illness': scenario['distribution']['acute_illness'],
        'emergencies': scenario['distribution']['emergencies'],
        'expected_duration_minutes': scenario['expected_duration_minutes'],
        'avg_consultation_time_minutes': scenario['avg_consultation_time_minutes'],
    }

    return ClinicDay(
        scenario_name=scenario_name,
        date=clinic_date,
        patients=patients,
        visits=visits,
        investigations=investigations,
        vitals=vitals_list,
        statistics=statistics
    )


def get_scenario_by_type(scenario_type: str) -> Dict:
    """Get scenario by type (busy, emergency, specialized, etc.)."""
    type_mapping = {
        'busy': ['busy_monday_morning', 'post_holiday_rush', 'flu_season'],
        'quiet': ['quiet_sunday'],
        'emergency': ['night_emergency_shift'],
        'specialized': ['diabetes_screening_camp', 'pediatric_vaccination_day',
                       'senior_citizen_clinic', 'antenatal_clinic'],
        'seasonal': ['flu_season', 'monsoon_clinic'],
    }

    scenarios = type_mapping.get(scenario_type, [])
    return {name: SCENARIOS[name] for name in scenarios if name in SCENARIOS}


def generate_weekly_schedule(week_start: date = None, seed: int = None) -> Dict[str, ClinicDay]:
    """Generate a complete week's schedule.

    Args:
        week_start: Start date of the week (Monday)
        seed: Random seed

    Returns:
        Dict mapping day names to ClinicDay objects
    """
    if week_start is None:
        # Get the Monday of current week
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    weekly_scenarios = {
        'Monday': 'busy_monday_morning',
        'Tuesday': 'flu_season',
        'Wednesday': 'senior_citizen_clinic',
        'Thursday': 'busy_monday_morning',
        'Friday': 'pediatric_vaccination_day',
        'Saturday': 'antenatal_clinic',
        'Sunday': 'quiet_sunday',
    }

    schedule = {}
    for i, (day_name, scenario_name) in enumerate(weekly_scenarios.items()):
        day_date = week_start + timedelta(days=i)
        day_seed = seed + i if seed else None

        clinic_day = generate_clinic_day(
            scenario_name=scenario_name,
            clinic_date=day_date,
            seed=day_seed
        )

        schedule[day_name] = clinic_day

    return schedule


def generate_monthly_statistics(month: int = None, year: int = None) -> Dict:
    """Generate statistics for a complete month.

    Args:
        month: Month number (1-12)
        year: Year

    Returns:
        Dict with monthly statistics
    """
    if month is None:
        month = date.today().month
    if year is None:
        year = date.today().year

    # Approximate days in month
    days_in_month = 30

    # Average patients per day based on day of week
    weekly_pattern = {
        0: 25,  # Monday (busy)
        1: 22,  # Tuesday
        2: 20,  # Wednesday
        3: 22,  # Thursday
        4: 24,  # Friday
        5: 15,  # Saturday
        6: 8,   # Sunday
    }

    total_patients = 0
    for day in range(days_in_month):
        day_of_week = day % 7
        total_patients += weekly_pattern[day_of_week]

    statistics = {
        'month': month,
        'year': year,
        'total_patients': total_patients,
        'avg_patients_per_day': total_patients / days_in_month,
        'busiest_day': 'Monday',
        'quietest_day': 'Sunday',
        'estimated_routine_followup': int(total_patients * 0.48),
        'estimated_new_patients': int(total_patients * 0.20),
        'estimated_acute_illness': int(total_patients * 0.24),
        'estimated_emergencies': int(total_patients * 0.08),
    }

    return statistics


__all__ = [
    "SCENARIOS",
    "ClinicDay",
    "generate_clinic_day",
    "get_scenario_by_type",
    "generate_weekly_schedule",
    "generate_monthly_statistics",
]
