"""Medical abbreviations dictionary and expansion logic for Indian clinical context.

Handles 50+ common medical abbreviations used in Indian clinical practice.
"""

from typing import Dict, Optional, List, Tuple
import re


# Comprehensive medical abbreviations mapping
MEDICAL_ABBREVIATIONS: Dict[str, str] = {
    # Chief complaint and history markers
    "c/o": "complaining of",
    "c/o/": "complaining of",
    "h/o": "history of",
    "h/o/": "history of",
    "k/c": "known case of",
    "k/c/o": "known case of",
    "s/o": "suggestive of",
    "s/p": "status post",
    "p/o": "per oral",
    "p/w": "presented with",

    # Examination abbreviations
    "o/e": "on examination",
    "p/e": "physical examination",
    "RS": "respiratory system",
    "CVS": "cardiovascular system",
    "CNS": "central nervous system",
    "P/A": "per abdomen",
    "PA": "per abdomen",
    "NAD": "no abnormality detected",
    "WNL": "within normal limits",

    # Common diagnoses
    "DM": "diabetes mellitus",
    "DM1": "type 1 diabetes mellitus",
    "DM2": "type 2 diabetes mellitus",
    "T2DM": "type 2 diabetes mellitus",
    "HTN": "hypertension",
    "IHD": "ischemic heart disease",
    "CAD": "coronary artery disease",
    "CVA": "cerebrovascular accident",
    "CKD": "chronic kidney disease",
    "COPD": "chronic obstructive pulmonary disease",
    "TB": "tuberculosis",
    "PTB": "pulmonary tuberculosis",
    "GERD": "gastroesophageal reflux disease",
    "UTI": "urinary tract infection",
    "ACS": "acute coronary syndrome",
    "MI": "myocardial infarction",
    "CCF": "congestive cardiac failure",
    "AF": "atrial fibrillation",
    "CHF": "congestive heart failure",
    "CRF": "chronic renal failure",
    "ARF": "acute renal failure",
    "URTI": "upper respiratory tract infection",
    "LRTI": "lower respiratory tract infection",

    # Vitals and measurements
    "BP": "blood pressure",
    "PR": "pulse rate",
    "HR": "heart rate",
    "RR": "respiratory rate",
    "temp": "temperature",
    "wt": "weight",
    "ht": "height",
    "SpO2": "oxygen saturation",

    # Medication frequency
    "OD": "once daily",
    "BD": "twice daily",
    "TDS": "thrice daily",
    "QID": "four times daily",
    "HS": "at bedtime",
    "SOS": "as needed",
    "PRN": "as needed",
    "stat": "immediately",
    "AC": "before meals",
    "PC": "after meals",
    "IM": "intramuscular",
    "IV": "intravenous",
    "SC": "subcutaneous",
    "PO": "per oral",

    # Investigations
    "CBC": "complete blood count",
    "RBS": "random blood sugar",
    "FBS": "fasting blood sugar",
    "PPBS": "post-prandial blood sugar",
    "HbA1c": "glycated hemoglobin",
    "LFT": "liver function test",
    "KFT": "kidney function test",
    "RFT": "renal function test",
    "ECG": "electrocardiogram",
    "EKG": "electrocardiogram",
    "CXR": "chest X-ray",
    "USG": "ultrasonography",
    "CT": "computed tomography",
    "MRI": "magnetic resonance imaging",
    "ECHO": "echocardiography",
    "TMT": "treadmill test",
    "PFT": "pulmonary function test",

    # Other common abbreviations
    "Dx": "diagnosis",
    "Rx": "prescription",
    "Tx": "treatment",
    "Sx": "symptoms",
    "Hx": "history",
    "NKDA": "no known drug allergies",
    "r/o": "rule out",
    "w/": "with",
    "w/o": "without",
    "b/l": "bilateral",
    "SOB": "shortness of breath",
}

# Additional Hinglish-to-English translations
HINGLISH_TERMS: Dict[str, str] = {
    "bukhar": "fever",
    "dard": "pain",
    "khasi": "cough",
    "khansi": "cough",
    "saans": "breathing",
    "ulti": "vomiting",
    "dast": "diarrhea",
    "loose motion": "diarrhea",
    "chakkar": "dizziness",
    "kamzori": "weakness",
    "kamjori": "weakness",
    "pet dard": "abdominal pain",
    "pet mein dard": "abdominal pain",
    "sir dard": "headache",
    "sar dard": "headache",
    "seene mein dard": "chest pain",
    "pet kharab": "upset stomach",
    "gas": "flatulence",
    "acidity": "acidity",
    "neend nahi aati": "insomnia",
    "bhook nahi lagti": "loss of appetite",
    "thakan": "fatigue",
}

# Contextual abbreviations (require context to expand properly)
CONTEXTUAL_ABBREVIATIONS = {
    "AC": ["before meals", "air conditioning"],  # Context dependent
    "PC": ["after meals", "personal computer"],
    "CVS": ["cardiovascular system", "chorionic villus sampling"],
}


def expand_abbreviation(abbr: str, context: Optional[str] = None) -> Optional[str]:
    """
    Expand a medical abbreviation to its full form.

    Args:
        abbr: The abbreviation to expand
        context: Optional context to help with ambiguous abbreviations

    Returns:
        Expanded form or None if not found
    """
    # Normalize abbreviation
    abbr_normalized = abbr.strip().upper()
    abbr_lower = abbr.strip().lower()

    # Check exact match (case-insensitive)
    for key, value in MEDICAL_ABBREVIATIONS.items():
        if key.upper() == abbr_normalized or key.lower() == abbr_lower:
            return value

    # Check Hinglish terms
    for key, value in HINGLISH_TERMS.items():
        if key.lower() == abbr_lower:
            return value

    # Handle contextual abbreviations
    if abbr_normalized in CONTEXTUAL_ABBREVIATIONS and context:
        possible_expansions = CONTEXTUAL_ABBREVIATIONS[abbr_normalized]
        # Use simple heuristics for context
        context_lower = context.lower()
        if "meal" in context_lower or "food" in context_lower:
            return possible_expansions[0]
        # Return most common medical meaning by default
        return possible_expansions[0]

    return None


def expand_text(text: str, preserve_case: bool = True) -> str:
    """
    Expand all abbreviations in a text.

    Args:
        text: Input text with abbreviations
        preserve_case: Whether to preserve original case

    Returns:
        Text with abbreviations expanded
    """
    result = text

    # Sort by length (descending) to handle longer abbreviations first
    all_abbrevs = list(MEDICAL_ABBREVIATIONS.keys()) + list(HINGLISH_TERMS.keys())
    all_abbrevs.sort(key=len, reverse=True)

    for abbr in all_abbrevs:
        # Create pattern that matches word boundaries
        pattern = r'\b' + re.escape(abbr) + r'\b'

        # Get expansion
        expansion = MEDICAL_ABBREVIATIONS.get(abbr) or HINGLISH_TERMS.get(abbr)

        if expansion:
            # Replace with case preservation if requested
            if preserve_case:
                # Check if abbreviation is uppercase
                if abbr.isupper():
                    expansion_cased = expansion.title()
                else:
                    expansion_cased = expansion
                result = re.sub(pattern, expansion_cased, result, flags=re.IGNORECASE)
            else:
                result = re.sub(pattern, expansion, result, flags=re.IGNORECASE)

    return result


def get_abbreviation_hints(partial: str, limit: int = 10) -> List[Tuple[str, str]]:
    """
    Get abbreviation suggestions based on partial input.

    Args:
        partial: Partial abbreviation to search for
        limit: Maximum number of hints to return

    Returns:
        List of (abbreviation, expansion) tuples
    """
    partial_lower = partial.lower()
    hints = []

    # Search in medical abbreviations
    for abbr, expansion in MEDICAL_ABBREVIATIONS.items():
        if abbr.lower().startswith(partial_lower):
            hints.append((abbr, expansion))

    # Search in Hinglish terms
    for term, expansion in HINGLISH_TERMS.items():
        if term.lower().startswith(partial_lower):
            hints.append((term, expansion))

    return hints[:limit]


def is_medical_abbreviation(text: str) -> bool:
    """
    Check if text is a known medical abbreviation.

    Args:
        text: Text to check

    Returns:
        True if it's a known abbreviation
    """
    text_normalized = text.strip().lower()

    # Check medical abbreviations
    for abbr in MEDICAL_ABBREVIATIONS.keys():
        if abbr.lower() == text_normalized:
            return True

    # Check Hinglish terms
    for term in HINGLISH_TERMS.keys():
        if term.lower() == text_normalized:
            return True

    return False


def get_all_abbreviations() -> Dict[str, str]:
    """
    Get combined dictionary of all abbreviations.

    Returns:
        Dictionary of all abbreviations and their expansions
    """
    return {**MEDICAL_ABBREVIATIONS, **HINGLISH_TERMS}
