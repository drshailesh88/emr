"""
Specialty-Specific Clinical Protocols

This module provides evidence-based treatment protocols for major medical specialties
commonly seen in Indian medical practice.

Available Protocols:
- Cardiology: ACS, Heart Failure, Atrial Fibrillation, Hypertension
- Pediatrics: Gastroenteritis, Pneumonia, Fever, Dengue, Asthma
- OB/GYN: Antenatal Care, GDM, Preeclampsia, PCOS, Menopause

Usage:
    from src.services.diagnosis.specialty_protocols import CardiologyProtocols

    cardio = CardiologyProtocols()
    stemi_protocol = cardio.get_protocol("stemi")
    compliance = cardio.check_compliance(prescription, "stemi")
"""

from .cardiology_protocols import CardiologyProtocols, RedFlag as CardiacRedFlag
from .pediatric_protocols import PediatricProtocols, RedFlag as PediatricRedFlag, GrowthAssessment
from .obgyn_protocols import OBGYNProtocols, RedFlag as OBGYNRedFlag, ANCVisit
from .protocol_calculator import (
    ProtocolCalculator,
    Dose,
    CVDRiskResult,
    Gender,
)

__all__ = [
    # Protocol classes
    "CardiologyProtocols",
    "PediatricProtocols",
    "OBGYNProtocols",

    # Calculators
    "ProtocolCalculator",

    # Data classes
    "CardiacRedFlag",
    "PediatricRedFlag",
    "OBGYNRedFlag",
    "GrowthAssessment",
    "ANCVisit",
    "Dose",
    "CVDRiskResult",
    "Gender",
]
