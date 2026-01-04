"""Clinical NLP Engine for DocAssist EMR.

Provides comprehensive natural language processing for clinical documentation:
- Extract structured SOAP notes from natural language transcripts
- Recognize medical entities (symptoms, diagnoses, medications, procedures)
- Generate differential diagnoses using Bayesian reasoning
- Suggest appropriate investigations
- Flag clinical red flags requiring immediate attention

Designed for Indian healthcare context with support for:
- Hindi, English, and code-mixed (Hinglish) speech
- Indian medical terminology and abbreviations
- India-specific disease prevalence for Bayesian priors
- Common Indian drug brands and generics
"""

from .entities import (
    # Core entities
    Symptom,
    Diagnosis,
    Drug,
    Investigation,
    Procedure,
    VitalSign,
    SOAPNote,
    Differential,
    RedFlag,
    ClinicalContext,

    # Enums
    Severity,
    Onset,
)

from .note_extractor import ClinicalNoteExtractor
from .medical_entity_recognition import MedicalNER
from .clinical_reasoning import ClinicalReasoning


__all__ = [
    # Main classes
    "ClinicalNoteExtractor",
    "MedicalNER",
    "ClinicalReasoning",

    # Entity classes
    "Symptom",
    "Diagnosis",
    "Drug",
    "Investigation",
    "Procedure",
    "VitalSign",
    "SOAPNote",
    "Differential",
    "RedFlag",
    "ClinicalContext",

    # Enums
    "Severity",
    "Onset",
]


# Version info
__version__ = "1.0.0"
__author__ = "DocAssist Team"
__description__ = "Clinical NLP Engine for Indian Healthcare"
