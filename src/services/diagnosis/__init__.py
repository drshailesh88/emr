"""
Diagnosis Engine for DocAssist EMR

Provides differential diagnosis, red flag detection, and treatment protocols
optimized for Indian medical practice.
"""

from .differential_engine import DifferentialEngine, Differential
from .red_flag_detector import RedFlagDetector, RedFlag, UrgencyLevel
from .protocol_engine import (
    ProtocolEngine,
    TreatmentProtocol,
    ComplianceReport,
    Medication,
)

__all__ = [
    "DifferentialEngine",
    "Differential",
    "RedFlagDetector",
    "RedFlag",
    "UrgencyLevel",
    "ProtocolEngine",
    "TreatmentProtocol",
    "ComplianceReport",
    "Medication",
]
