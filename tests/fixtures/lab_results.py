"""Lab result fixtures for DocAssist EMR testing."""

import random
from datetime import date, timedelta
from typing import List, Dict, Tuple
from src.models.schemas import Investigation


# ============== LAB RESULT FIXTURES ==============

LAB_RESULTS = {
    # Complete Blood Count
    'normal_cbc': [
        Investigation(
            patient_id=1,
            test_name="Hemoglobin",
            result="14.5",
            unit="g/dL",
            reference_range="13-17 (M), 12-15 (F)",
            test_date=date.today(),
            is_abnormal=False
        ),
        Investigation(
            patient_id=1,
            test_name="Total WBC Count",
            result="8500",
            unit="/cumm",
            reference_range="4000-11000",
            test_date=date.today(),
            is_abnormal=False
        ),
        Investigation(
            patient_id=1,
            test_name="Platelet Count",
            result="250000",
            unit="/cumm",
            reference_range="150000-450000",
            test_date=date.today(),
            is_abnormal=False
        ),
    ],

    'anemia': [
        Investigation(
            patient_id=5,
            test_name="Hemoglobin",
            result="8.5",
            unit="g/dL",
            reference_range="13-17 (M), 12-15 (F)",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=5,
            test_name="MCV",
            result="68",
            unit="fL",
            reference_range="80-100",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=5,
            test_name="Iron",
            result="25",
            unit="mcg/dL",
            reference_range="60-170",
            test_date=date.today(),
            is_abnormal=True
        ),
    ],

    # Diabetes markers
    'diabetic_hba1c_high': Investigation(
        patient_id=2,
        test_name="HbA1c",
        result="9.5",
        unit="%",
        reference_range="<5.7 (normal), 5.7-6.4 (pre-diabetic), >6.5 (diabetic)",
        test_date=date.today(),
        is_abnormal=True
    ),

    'diabetic_hba1c_controlled': Investigation(
        patient_id=1,
        test_name="HbA1c",
        result="6.8",
        unit="%",
        reference_range="<5.7 (normal), 5.7-6.4 (pre-diabetic), >6.5 (diabetic)",
        test_date=date.today(),
        is_abnormal=False
    ),

    'normal_fbs': Investigation(
        patient_id=1,
        test_name="Fasting Blood Sugar",
        result="95",
        unit="mg/dL",
        reference_range="70-110",
        test_date=date.today(),
        is_abnormal=False
    ),

    'high_fbs': Investigation(
        patient_id=2,
        test_name="Fasting Blood Sugar",
        result="185",
        unit="mg/dL",
        reference_range="70-110",
        test_date=date.today(),
        is_abnormal=True
    ),

    # Kidney function
    'renal_impairment': [
        Investigation(
            patient_id=5,
            test_name="Serum Creatinine",
            result="3.2",
            unit="mg/dL",
            reference_range="0.7-1.3",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=5,
            test_name="Blood Urea",
            result="85",
            unit="mg/dL",
            reference_range="15-40",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=5,
            test_name="eGFR",
            result="22",
            unit="ml/min/1.73m²",
            reference_range=">60",
            test_date=date.today(),
            is_abnormal=True
        ),
    ],

    'normal_kidney_function': [
        Investigation(
            patient_id=1,
            test_name="Serum Creatinine",
            result="1.0",
            unit="mg/dL",
            reference_range="0.7-1.3",
            test_date=date.today(),
            is_abnormal=False
        ),
        Investigation(
            patient_id=1,
            test_name="Blood Urea",
            result="28",
            unit="mg/dL",
            reference_range="15-40",
            test_date=date.today(),
            is_abnormal=False
        ),
    ],

    # Liver function
    'liver_dysfunction': [
        Investigation(
            patient_id=10,
            test_name="SGOT (AST)",
            result="125",
            unit="U/L",
            reference_range="5-40",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=10,
            test_name="SGPT (ALT)",
            result="185",
            unit="U/L",
            reference_range="5-40",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=10,
            test_name="Total Bilirubin",
            result="2.5",
            unit="mg/dL",
            reference_range="0.3-1.2",
            test_date=date.today(),
            is_abnormal=True
        ),
    ],

    'normal_liver_function': [
        Investigation(
            patient_id=1,
            test_name="SGOT (AST)",
            result="28",
            unit="U/L",
            reference_range="5-40",
            test_date=date.today(),
            is_abnormal=False
        ),
        Investigation(
            patient_id=1,
            test_name="SGPT (ALT)",
            result="32",
            unit="U/L",
            reference_range="5-40",
            test_date=date.today(),
            is_abnormal=False
        ),
    ],

    # Critical values
    'critical_potassium_high': Investigation(
        patient_id=5,
        test_name="Serum Potassium",
        result="6.8",
        unit="mEq/L",
        reference_range="3.5-5.0",
        test_date=date.today(),
        is_abnormal=True
    ),

    'critical_potassium_low': Investigation(
        patient_id=11,
        test_name="Serum Potassium",
        result="2.5",
        unit="mEq/L",
        reference_range="3.5-5.0",
        test_date=date.today(),
        is_abnormal=True
    ),

    'critical_sodium_low': Investigation(
        patient_id=12,
        test_name="Serum Sodium",
        result="118",
        unit="mEq/L",
        reference_range="135-145",
        test_date=date.today(),
        is_abnormal=True
    ),

    # Lipid profile
    'dyslipidemia': [
        Investigation(
            patient_id=4,
            test_name="Total Cholesterol",
            result="265",
            unit="mg/dL",
            reference_range="<200",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=4,
            test_name="LDL Cholesterol",
            result="175",
            unit="mg/dL",
            reference_range="<100",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=4,
            test_name="HDL Cholesterol",
            result="32",
            unit="mg/dL",
            reference_range=">40 (M), >50 (F)",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=4,
            test_name="Triglycerides",
            result="285",
            unit="mg/dL",
            reference_range="<150",
            test_date=date.today(),
            is_abnormal=True
        ),
    ],

    # Thyroid
    'hypothyroid': [
        Investigation(
            patient_id=24,
            test_name="TSH",
            result="12.5",
            unit="mIU/L",
            reference_range="0.5-5.0",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=24,
            test_name="Free T4",
            result="0.6",
            unit="ng/dL",
            reference_range="0.8-2.0",
            test_date=date.today(),
            is_abnormal=True
        ),
    ],

    'hyperthyroid': [
        Investigation(
            patient_id=25,
            test_name="TSH",
            result="0.05",
            unit="mIU/L",
            reference_range="0.5-5.0",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=25,
            test_name="Free T4",
            result="3.5",
            unit="ng/dL",
            reference_range="0.8-2.0",
            test_date=date.today(),
            is_abnormal=True
        ),
    ],

    # Cardiac markers
    'elevated_troponin': Investigation(
        patient_id=4,
        test_name="Troponin I",
        result="2.5",
        unit="ng/mL",
        reference_range="<0.04",
        test_date=date.today(),
        is_abnormal=True
    ),

    # Infection markers
    'infection_markers_high': [
        Investigation(
            patient_id=15,
            test_name="Total WBC Count",
            result="18500",
            unit="/cumm",
            reference_range="4000-11000",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=15,
            test_name="Neutrophils",
            result="85",
            unit="%",
            reference_range="40-70",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=15,
            test_name="ESR",
            result="65",
            unit="mm/hr",
            reference_range="0-20",
            test_date=date.today(),
            is_abnormal=True
        ),
        Investigation(
            patient_id=15,
            test_name="CRP",
            result="85",
            unit="mg/L",
            reference_range="<5",
            test_date=date.today(),
            is_abnormal=True
        ),
    ],

    # Coagulation
    'inr_therapeutic': Investigation(
        patient_id=3,
        test_name="INR",
        result="2.5",
        unit="",
        reference_range="0.8-1.2 (normal), 2.0-3.0 (therapeutic for AF)",
        test_date=date.today(),
        is_abnormal=False  # Therapeutic, so not abnormal
    ),

    'inr_supratherapeutic': Investigation(
        patient_id=3,
        test_name="INR",
        result="4.5",
        unit="",
        reference_range="0.8-1.2 (normal), 2.0-3.0 (therapeutic for AF)",
        test_date=date.today(),
        is_abnormal=True
    ),
}


# ============== LAB RESULT GENERATORS ==============

def create_lab_result(patient_id: int,
                     test_name: str,
                     result: str,
                     unit: str,
                     reference_range: str,
                     is_abnormal: bool = False,
                     test_date: date = None) -> Investigation:
    """Create a single lab result."""
    if test_date is None:
        test_date = date.today()

    return Investigation(
        patient_id=patient_id,
        test_name=test_name,
        result=result,
        unit=unit,
        reference_range=reference_range,
        test_date=test_date,
        is_abnormal=is_abnormal
    )


def generate_lab_history(patient_id: int,
                        test_name: str,
                        months: int = 6,
                        trend: str = "stable") -> List[Investigation]:
    """Generate lab history showing trends over time.

    Args:
        patient_id: Patient ID
        test_name: Name of the test (e.g., "HbA1c", "Creatinine")
        months: Number of months of history
        trend: "improving", "worsening", "stable", "fluctuating"

    Returns:
        List of Investigation objects
    """
    test_configs = {
        "HbA1c": {
            "unit": "%",
            "reference_range": "<5.7 (normal), 5.7-6.4 (pre-diabetic), >6.5 (diabetic)",
            "normal_range": (5.5, 6.5),
            "abnormal_range": (7.0, 10.0)
        },
        "Creatinine": {
            "unit": "mg/dL",
            "reference_range": "0.7-1.3",
            "normal_range": (0.8, 1.2),
            "abnormal_range": (1.5, 4.0)
        },
        "Fasting Blood Sugar": {
            "unit": "mg/dL",
            "reference_range": "70-110",
            "normal_range": (85, 110),
            "abnormal_range": (130, 220)
        },
        "LDL Cholesterol": {
            "unit": "mg/dL",
            "reference_range": "<100",
            "normal_range": (70, 100),
            "abnormal_range": (120, 200)
        },
        "Hemoglobin": {
            "unit": "g/dL",
            "reference_range": "13-17 (M), 12-15 (F)",
            "normal_range": (12.5, 15.0),
            "abnormal_range": (8.0, 11.5)
        }
    }

    config = test_configs.get(test_name)
    if not config:
        return []

    results = []
    base_date = date.today() - timedelta(days=30 * months)

    # Generate values based on trend
    for i in range(months):
        test_date = base_date + timedelta(days=30 * i)

        if trend == "improving":
            # Start abnormal, move toward normal
            progress = i / (months - 1) if months > 1 else 0
            start_val = random.uniform(*config["abnormal_range"])
            end_val = random.uniform(*config["normal_range"])
            value = start_val + (end_val - start_val) * progress

        elif trend == "worsening":
            # Start normal, move toward abnormal
            progress = i / (months - 1) if months > 1 else 0
            start_val = random.uniform(*config["normal_range"])
            end_val = random.uniform(*config["abnormal_range"])
            value = start_val + (end_val - start_val) * progress

        elif trend == "fluctuating":
            # Randomly pick normal or abnormal
            if random.random() < 0.5:
                value = random.uniform(*config["normal_range"])
            else:
                value = random.uniform(*config["abnormal_range"])

        else:  # stable
            # Stay in one range
            if random.random() < 0.7:  # 70% normal
                value = random.uniform(*config["normal_range"])
            else:
                value = random.uniform(*config["abnormal_range"])

        # Determine if abnormal
        is_abnormal = not (config["normal_range"][0] <= value <= config["normal_range"][1])

        result = Investigation(
            patient_id=patient_id,
            test_name=test_name,
            result=f"{value:.1f}",
            unit=config["unit"],
            reference_range=config["reference_range"],
            test_date=test_date,
            is_abnormal=is_abnormal
        )
        results.append(result)

    return results


def generate_complete_metabolic_panel(patient_id: int,
                                     is_abnormal: bool = False) -> List[Investigation]:
    """Generate a complete metabolic panel."""
    if is_abnormal:
        return [
            create_lab_result(patient_id, "Serum Sodium", "128", "mEq/L", "135-145", True),
            create_lab_result(patient_id, "Serum Potassium", "5.8", "mEq/L", "3.5-5.0", True),
            create_lab_result(patient_id, "Serum Chloride", "95", "mEq/L", "98-107", True),
            create_lab_result(patient_id, "Serum Bicarbonate", "18", "mEq/L", "22-28", True),
            create_lab_result(patient_id, "Blood Urea", "75", "mg/dL", "15-40", True),
            create_lab_result(patient_id, "Serum Creatinine", "2.8", "mg/dL", "0.7-1.3", True),
            create_lab_result(patient_id, "Blood Glucose", "185", "mg/dL", "70-110", True),
        ]
    else:
        return [
            create_lab_result(patient_id, "Serum Sodium", "138", "mEq/L", "135-145", False),
            create_lab_result(patient_id, "Serum Potassium", "4.2", "mEq/L", "3.5-5.0", False),
            create_lab_result(patient_id, "Serum Chloride", "102", "mEq/L", "98-107", False),
            create_lab_result(patient_id, "Serum Bicarbonate", "25", "mEq/L", "22-28", False),
            create_lab_result(patient_id, "Blood Urea", "28", "mg/dL", "15-40", False),
            create_lab_result(patient_id, "Serum Creatinine", "1.0", "mg/dL", "0.7-1.3", False),
            create_lab_result(patient_id, "Blood Glucose", "95", "mg/dL", "70-110", False),
        ]


def get_critical_lab_results() -> Dict[str, Investigation]:
    """Get all critical lab results that need immediate attention."""
    return {
        "critical_hyperkalemia": LAB_RESULTS["critical_potassium_high"],
        "critical_hypokalemia": LAB_RESULTS["critical_potassium_low"],
        "critical_hyponatremia": LAB_RESULTS["critical_sodium_low"],
        "critical_troponin": LAB_RESULTS["elevated_troponin"],
        "critical_inr": LAB_RESULTS["inr_supratherapeutic"],
    }


def generate_diabetes_monitoring_labs(patient_id: int,
                                      months: int = 12) -> List[Investigation]:
    """Generate typical diabetes monitoring labs over time."""
    labs = []

    # HbA1c every 3 months
    for i in range(0, months, 3):
        test_date = date.today() - timedelta(days=30 * (months - i))
        value = random.uniform(6.5, 8.5)
        labs.append(Investigation(
            patient_id=patient_id,
            test_name="HbA1c",
            result=f"{value:.1f}",
            unit="%",
            reference_range="<5.7 (normal), 5.7-6.4 (pre-diabetic), >6.5 (diabetic)",
            test_date=test_date,
            is_abnormal=(value > 7.0)
        ))

    # Monthly FBS
    for i in range(months):
        test_date = date.today() - timedelta(days=30 * (months - i - 1))
        value = random.uniform(110, 160)
        labs.append(Investigation(
            patient_id=patient_id,
            test_name="Fasting Blood Sugar",
            result=f"{value:.0f}",
            unit="mg/dL",
            reference_range="70-110",
            test_date=test_date,
            is_abnormal=(value > 125)
        ))

    return labs


__all__ = [
    "LAB_RESULTS",
    "create_lab_result",
    "generate_lab_history",
    "generate_complete_metabolic_panel",
    "get_critical_lab_results",
    "generate_diabetes_monitoring_labs",
]
