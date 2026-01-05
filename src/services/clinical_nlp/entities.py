"""Clinical NLP entity dataclasses for structured clinical data extraction."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict
from enum import Enum


class Severity(str, Enum):
    """Symptom/finding severity levels."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class Onset(str, Enum):
    """Symptom onset patterns."""
    ACUTE = "acute"  # < 24 hours
    SUBACUTE = "subacute"  # 1-7 days
    CHRONIC = "chronic"  # > 7 days
    GRADUAL = "gradual"
    SUDDEN = "sudden"


@dataclass
class Symptom:
    """Extracted symptom with clinical context."""
    name: str
    duration: Optional[str] = None  # "3 days", "2 weeks"
    severity: Optional[Severity] = None
    onset: Optional[Onset] = None
    aggravating_factors: List[str] = field(default_factory=list)
    relieving_factors: List[str] = field(default_factory=list)
    associated_symptoms: List[str] = field(default_factory=list)
    location: Optional[str] = None  # For pain/localized symptoms
    quality: Optional[str] = None  # "sharp", "dull", "throbbing"
    radiation: Optional[str] = None  # For pain radiation
    timing: Optional[str] = None  # "morning", "after meals"
    context: Optional[str] = None  # Full text context where found


@dataclass
class Diagnosis:
    """Extracted diagnosis with ICD-10 mapping."""
    name: str
    icd10_code: Optional[str] = None
    confidence: float = 1.0  # 0-1 scale
    is_primary: bool = False
    is_differential: bool = False
    supporting_evidence: List[str] = field(default_factory=list)
    context: Optional[str] = None


@dataclass
class Drug:
    """Extracted medication with complete dosing information."""
    name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    dose: Optional[str] = None
    strength: Optional[str] = None
    route: str = "oral"  # oral, IV, IM, SC, topical, etc.
    frequency: Optional[str] = None  # OD, BD, TDS, QID, HS, SOS, stat
    duration: Optional[str] = None
    instructions: Optional[str] = None  # "with food", "before meals"
    reason: Optional[str] = None  # Indication
    context: Optional[str] = None


@dataclass
class Investigation:
    """Extracted investigation/lab test."""
    name: str
    test_type: str  # "lab", "imaging", "procedure"
    urgency: str = "routine"  # stat, urgent, routine
    reason: Optional[str] = None
    timing: Optional[str] = None  # "fasting", "post-prandial"
    context: Optional[str] = None


@dataclass
class Procedure:
    """Extracted procedure."""
    name: str
    procedure_type: str  # "diagnostic", "therapeutic", "surgical"
    indication: Optional[str] = None
    date_performed: Optional[date] = None
    outcome: Optional[str] = None
    complications: List[str] = field(default_factory=list)
    context: Optional[str] = None


@dataclass
class VitalSign:
    """Individual vital sign measurement."""
    name: str
    value: str
    unit: str
    is_abnormal: bool = False
    context: Optional[str] = None


@dataclass
class SOAPNote:
    """Structured SOAP note extracted from transcript."""

    # Subjective
    chief_complaint: str = ""
    history_of_present_illness: str = ""
    associated_symptoms: List[str] = field(default_factory=list)
    duration: Optional[str] = None
    severity: Optional[str] = None

    # Objective
    vitals: Dict[str, str] = field(default_factory=dict)  # {"BP": "120/80", "HR": "72"}
    examination_findings: List[str] = field(default_factory=list)
    significant_findings: List[str] = field(default_factory=list)

    # Assessment
    diagnoses: List[str] = field(default_factory=list)
    differential_diagnoses: List[str] = field(default_factory=list)
    clinical_impression: str = ""

    # Plan
    medications: List[Drug] = field(default_factory=list)
    investigations: List[Investigation] = field(default_factory=list)
    procedures: List[Procedure] = field(default_factory=list)
    advice: List[str] = field(default_factory=list)
    follow_up: Optional[str] = None
    referrals: List[str] = field(default_factory=list)

    # Metadata
    extracted_at: datetime = field(default_factory=datetime.now)
    confidence_score: float = 1.0
    raw_transcript: Optional[str] = None


@dataclass
class Differential:
    """Differential diagnosis with probability."""
    diagnosis: str
    icd10_code: Optional[str] = None
    probability: float = 0.5  # 0-1 scale (Bayesian posterior)
    prior_probability: float = 0.0  # India-specific prevalence
    supporting_features: List[str] = field(default_factory=list)
    against_features: List[str] = field(default_factory=list)
    recommended_investigations: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    treatment_urgency: str = "routine"  # stat, urgent, routine


@dataclass
class RedFlag:
    """Clinical red flag requiring immediate attention."""
    category: str  # "cardiac", "neuro", "sepsis", "hemorrhage", etc.
    description: str
    severity: Severity
    action_required: str
    time_critical: bool = False
    system: Optional[str] = None  # "cardiovascular", "respiratory", etc.


@dataclass
class ClinicalContext:
    """Full clinical context for reasoning."""
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    known_conditions: List[str] = field(default_factory=list)
    current_medications: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    past_surgeries: List[str] = field(default_factory=list)
    family_history: List[str] = field(default_factory=list)
    social_history: Dict[str, str] = field(default_factory=dict)
    recent_labs: Dict[str, str] = field(default_factory=dict)
    recent_vitals: Dict[str, str] = field(default_factory=dict)
