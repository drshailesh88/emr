"""Clinical decision support rules and critical value definitions."""

from typing import Optional, Dict, Tuple


# Critical value thresholds based on spec
CRITICAL_VALUES = {
    "Potassium": {
        "critical_low": 2.5,
        "critical_high": 6.0,
        "unit": "mEq/L",
        "warning_message": "Risk of cardiac arrhythmia",
        "actions": [
            "Obtain ECG immediately",
            "Consider calcium gluconate if >6.5",
            "Review medications (ACE-I, K+ supplements, spironolactone)",
            "Consider insulin + dextrose or salbutamol if >6.5"
        ]
    },
    "Sodium": {
        "critical_low": 120,
        "critical_high": 160,
        "unit": "mEq/L",
        "warning_message": "Risk of seizures or neurological complications",
        "actions": [
            "Assess volume status",
            "Review fluid intake",
            "Check urine osmolality",
            "Consider 3% saline if symptomatic and <115"
        ]
    },
    "Glucose": {
        "critical_low": 50,
        "critical_high": 500,
        "unit": "mg/dL",
        "warning_message": "Risk of hypoglycemic shock or DKA",
        "actions": [
            "Check capillary glucose immediately",
            "If <50: Give 25g IV dextrose",
            "If >400: Check ketones, assess for DKA",
            "Review insulin/oral hypoglycemics"
        ]
    },
    "Hemoglobin": {
        "critical_low": 6,
        "critical_high": 20,
        "unit": "g/dL",
        "warning_message": "Risk of tissue hypoxia or polycythemia",
        "actions": [
            "If <7: Consider blood transfusion",
            "Assess for bleeding source",
            "Check iron studies, B12, folate",
            "If >18: Rule out polycythemia vera"
        ]
    },
    "Creatinine": {
        "critical_high": 10,
        "unit": "mg/dL",
        "warning_message": "Severe renal impairment",
        "actions": [
            "Check electrolytes (K+, acidosis)",
            "Assess for uremia symptoms",
            "Consider nephrology consult",
            "May need dialysis if symptomatic"
        ]
    },
    "INR": {
        "critical_high": 5.0,
        "warning_message": "High bleeding risk",
        "actions": [
            "Stop warfarin",
            "Assess for bleeding",
            "If bleeding: Give Vitamin K + PCC/FFP",
            "Recheck INR in 24 hours"
        ]
    },
    "Platelets": {
        "critical_low": 20000,
        "critical_high": 1000000,
        "unit": "/μL",
        "warning_message": "Risk of bleeding or thrombosis",
        "actions": [
            "If <20,000: Consider platelet transfusion",
            "Assess for bleeding signs",
            "Hold anticoagulants/antiplatelets",
            "If >1,000,000: Rule out myeloproliferative disorder"
        ]
    },
    "WBC": {
        "critical_low": 1000,
        "critical_high": 50000,
        "unit": "/μL",
        "warning_message": "Risk of infection or leukemia",
        "actions": [
            "If <1,000: Neutropenic precautions",
            "Check differential count",
            "Rule out sepsis if febrile",
            "If >50,000: Consider leukostasis, hematology consult"
        ]
    }
}


# Screening reminders (from flowsheets feature - future integration)
SCREENING_RULES = {
    "diabetes": {
        "HbA1c": {"frequency_months": 3, "description": "HbA1c every 3 months for diabetics"},
        "Foot Exam": {"frequency_months": 12, "description": "Annual diabetic foot exam"},
        "Eye Exam": {"frequency_months": 12, "description": "Annual retinal screening"}
    },
    "hypertension": {
        "ECG": {"frequency_months": 12, "description": "Annual ECG for hypertensives"},
        "Lipid Panel": {"frequency_months": 12, "description": "Annual lipid profile"}
    },
    "general": {
        "CBC": {"frequency_months": 12, "description": "Annual complete blood count"},
        "Renal Function": {"frequency_months": 12, "description": "Annual kidney function"}
    }
}


def check_critical_value(test_name: str, value: float) -> Optional[Dict]:
    """Check if a lab value is critical and return alert details.

    Args:
        test_name: Name of the test
        value: Numeric value

    Returns:
        Dict with alert details if critical, None otherwise
    """
    # Normalize test name (case-insensitive matching)
    test_key = None
    for key in CRITICAL_VALUES.keys():
        if key.lower() in test_name.lower() or test_name.lower() in key.lower():
            test_key = key
            break

    if not test_key:
        return None

    rule = CRITICAL_VALUES[test_key]
    critical_low = rule.get("critical_low")
    critical_high = rule.get("critical_high")

    is_critical = False
    direction = None

    if critical_low is not None and value < critical_low:
        is_critical = True
        direction = "LOW"
    elif critical_high is not None and value > critical_high:
        is_critical = True
        direction = "HIGH"

    if not is_critical:
        return None

    # Build alert message
    title = f"CRITICAL {direction} {test_key.upper()}"
    message = f"{test_key} = {value} {rule['unit']}\n\n"

    if direction == "LOW" and critical_low:
        message += f"Critical threshold: <{critical_low} {rule['unit']}\n\n"
    elif direction == "HIGH" and critical_high:
        message += f"Critical threshold: >{critical_high} {rule['unit']}\n\n"

    message += f"⚠️ {rule['warning_message']}\n\n"
    message += "Recommended Actions:\n"
    for action in rule['actions']:
        message += f"• {action}\n"

    return {
        "alert_type": "critical_lab",
        "severity": "critical",
        "title": title,
        "message": message.strip(),
        "test_name": test_key,
        "value": value,
        "unit": rule['unit'],
        "direction": direction
    }


def get_critical_value_range(test_name: str) -> Optional[Tuple[Optional[float], Optional[float], str]]:
    """Get critical value range for a test.

    Args:
        test_name: Name of the test

    Returns:
        Tuple of (critical_low, critical_high, unit) or None
    """
    test_key = None
    for key in CRITICAL_VALUES.keys():
        if key.lower() in test_name.lower() or test_name.lower() in key.lower():
            test_key = key
            break

    if not test_key:
        return None

    rule = CRITICAL_VALUES[test_key]
    return (
        rule.get("critical_low"),
        rule.get("critical_high"),
        rule.get("unit", "")
    )
