"""Reference ranges for common lab tests."""

from typing import Dict, Tuple, Optional

# Reference ranges: (min, max, unit)
# Values based on common Indian lab standards
REFERENCE_RANGES: Dict[str, Tuple[Optional[float], Optional[float], str]] = {
    # Renal Panel
    "Creatinine": (0.7, 1.3, "mg/dL"),
    "BUN": (7, 20, "mg/dL"),
    "eGFR": (90, None, "mL/min"),
    "Urea": (15, 40, "mg/dL"),
    "Potassium": (3.5, 5.0, "mEq/L"),
    "Sodium": (135, 145, "mEq/L"),
    "Chloride": (98, 107, "mEq/L"),

    # Diabetic Panel
    "FBS": (70, 100, "mg/dL"),
    "PPBS": (None, 140, "mg/dL"),
    "HbA1c": (4.0, 6.5, "%"),
    "Random Blood Sugar": (None, 140, "mg/dL"),

    # Lipid Panel
    "Total Cholesterol": (None, 200, "mg/dL"),
    "LDL": (None, 100, "mg/dL"),
    "HDL": (40, None, "mg/dL"),
    "Triglycerides": (None, 150, "mg/dL"),
    "VLDL": (None, 30, "mg/dL"),

    # Thyroid Panel
    "TSH": (0.4, 4.0, "mIU/L"),
    "T3": (80, 200, "ng/dL"),
    "T4": (4.5, 12.0, "μg/dL"),
    "Free T3": (2.3, 4.2, "pg/mL"),
    "Free T4": (0.8, 1.8, "ng/dL"),

    # Liver Panel
    "ALT": (None, 40, "U/L"),
    "AST": (None, 40, "U/L"),
    "ALP": (30, 120, "U/L"),
    "Bilirubin Total": (0.3, 1.2, "mg/dL"),
    "Bilirubin Direct": (None, 0.3, "mg/dL"),
    "Total Protein": (6.0, 8.3, "g/dL"),
    "Albumin": (3.5, 5.5, "g/dL"),

    # Cardiac Panel
    "Troponin I": (None, 0.04, "ng/mL"),
    "Troponin T": (None, 0.01, "ng/mL"),
    "BNP": (None, 100, "pg/mL"),
    "CK-MB": (None, 25, "U/L"),
    "CPK": (30, 200, "U/L"),

    # CBC
    "Hemoglobin": (13.0, 17.0, "g/dL"),  # Male
    "WBC": (4000, 11000, "cells/μL"),
    "Platelets": (150000, 450000, "cells/μL"),
    "RBC": (4.5, 6.5, "million/μL"),  # Male
    "Hematocrit": (40, 54, "%"),  # Male
    "MCV": (80, 100, "fL"),
    "MCH": (27, 32, "pg"),
    "MCHC": (32, 36, "g/dL"),
    "Neutrophils": (40, 70, "%"),
    "Lymphocytes": (20, 45, "%"),
    "Monocytes": (2, 10, "%"),
    "Eosinophils": (1, 6, "%"),
    "Basophils": (0, 2, "%"),

    # Uric Acid
    "Uric Acid": (3.5, 7.2, "mg/dL"),

    # Calcium & Vitamins
    "Calcium": (8.5, 10.5, "mg/dL"),
    "Phosphorus": (2.5, 4.5, "mg/dL"),
    "Magnesium": (1.7, 2.2, "mg/dL"),
    "Vitamin D": (30, 100, "ng/mL"),
    "Vitamin B12": (200, 900, "pg/mL"),

    # Hormones
    "Cortisol": (5, 25, "μg/dL"),
    "Prolactin": (None, 20, "ng/mL"),
    "Testosterone": (300, 1000, "ng/dL"),  # Male

    # Others
    "CRP": (None, 3.0, "mg/L"),
    "ESR": (None, 20, "mm/hr"),
    "PT": (11, 13.5, "sec"),
    "INR": (0.8, 1.2, ""),
    "APTT": (25, 35, "sec"),
}


# Trend panels configuration
TREND_PANELS = {
    "Renal": ["Creatinine", "BUN", "eGFR", "Potassium"],
    "Diabetic": ["FBS", "PPBS", "HbA1c"],
    "Lipid": ["Total Cholesterol", "LDL", "HDL", "Triglycerides"],
    "Thyroid": ["TSH", "T3", "T4"],
    "Liver": ["ALT", "AST", "ALP", "Bilirubin Total"],
    "Cardiac": ["Troponin I", "BNP", "CK-MB"],
    "CBC": ["Hemoglobin", "WBC", "Platelets"],
}


def get_reference_range(test_name: str) -> Tuple[Optional[float], Optional[float], str]:
    """
    Get reference range for a test.

    Args:
        test_name: Name of the test

    Returns:
        Tuple of (min, max, unit). min/max can be None if unbounded.
    """
    # Try exact match first
    if test_name in REFERENCE_RANGES:
        return REFERENCE_RANGES[test_name]

    # Try case-insensitive match
    test_lower = test_name.lower()
    for key, value in REFERENCE_RANGES.items():
        if key.lower() == test_lower:
            return value

    # Try partial match
    for key, value in REFERENCE_RANGES.items():
        if test_lower in key.lower() or key.lower() in test_lower:
            return value

    # No match found
    return (None, None, "")


def is_abnormal(test_name: str, value: float) -> bool:
    """
    Check if a test value is abnormal.

    Args:
        test_name: Name of the test
        value: Test value

    Returns:
        True if value is outside reference range
    """
    min_val, max_val, _ = get_reference_range(test_name)

    if min_val is not None and value < min_val:
        return True
    if max_val is not None and value > max_val:
        return True

    return False
