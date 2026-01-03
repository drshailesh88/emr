"""Safety framework for prescription and clinical decision validation.

This module provides hard-coded safety checks that OVERRIDE LLM suggestions.
These rules are critical for patient safety and should never be bypassed.
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import date

from ..models.schemas import (
    Prescription, Medication, PatientSnapshot, SafetyAlert
)


@dataclass
class DrugInfo:
    """Drug information for safety checks."""
    name: str
    max_daily_dose: Optional[float] = None
    max_single_dose: Optional[float] = None
    unit: str = "mg"
    renal_adjustment_egfr: Optional[int] = None  # eGFR threshold for adjustment
    hepatic_caution: bool = False
    pregnancy_category: str = "C"
    contraindicated_conditions: List[str] = None
    drug_class: str = ""

    def __post_init__(self):
        if self.contraindicated_conditions is None:
            self.contraindicated_conditions = []


# Common drug safety database (expandable)
DRUG_DATABASE: Dict[str, DrugInfo] = {
    # Diabetes medications
    "metformin": DrugInfo(
        name="Metformin",
        max_daily_dose=2550,
        unit="mg",
        renal_adjustment_egfr=30,
        contraindicated_conditions=["acute kidney injury", "metabolic acidosis", "severe hepatic impairment"],
        drug_class="biguanide"
    ),
    "glimepiride": DrugInfo(
        name="Glimepiride",
        max_daily_dose=8,
        unit="mg",
        renal_adjustment_egfr=60,
        drug_class="sulfonylurea"
    ),
    "sitagliptin": DrugInfo(
        name="Sitagliptin",
        max_daily_dose=100,
        unit="mg",
        renal_adjustment_egfr=45,
        drug_class="dpp4_inhibitor"
    ),

    # Cardiac medications
    "aspirin": DrugInfo(
        name="Aspirin",
        max_daily_dose=325,  # For cardiac use
        unit="mg",
        contraindicated_conditions=["active bleeding", "peptic ulcer"],
        drug_class="antiplatelet"
    ),
    "clopidogrel": DrugInfo(
        name="Clopidogrel",
        max_daily_dose=75,
        unit="mg",
        contraindicated_conditions=["active bleeding"],
        drug_class="antiplatelet"
    ),
    "atorvastatin": DrugInfo(
        name="Atorvastatin",
        max_daily_dose=80,
        unit="mg",
        hepatic_caution=True,
        drug_class="statin"
    ),
    "ramipril": DrugInfo(
        name="Ramipril",
        max_daily_dose=10,
        unit="mg",
        renal_adjustment_egfr=30,
        contraindicated_conditions=["bilateral renal artery stenosis", "angioedema"],
        drug_class="ace_inhibitor"
    ),

    # Pain medications
    "paracetamol": DrugInfo(
        name="Paracetamol",
        max_daily_dose=4000,
        max_single_dose=1000,
        unit="mg",
        hepatic_caution=True,
        drug_class="analgesic"
    ),
    "ibuprofen": DrugInfo(
        name="Ibuprofen",
        max_daily_dose=1200,
        unit="mg",
        renal_adjustment_egfr=30,
        contraindicated_conditions=["peptic ulcer", "renal impairment", "heart failure"],
        drug_class="nsaid"
    ),

    # Antibiotics
    "amoxicillin": DrugInfo(
        name="Amoxicillin",
        max_daily_dose=3000,
        unit="mg",
        renal_adjustment_egfr=30,
        drug_class="penicillin"
    ),
    "azithromycin": DrugInfo(
        name="Azithromycin",
        max_daily_dose=500,
        unit="mg",
        hepatic_caution=True,
        drug_class="macrolide"
    ),
    "ciprofloxacin": DrugInfo(
        name="Ciprofloxacin",
        max_daily_dose=1500,
        unit="mg",
        renal_adjustment_egfr=30,
        contraindicated_conditions=["myasthenia gravis", "tendon disorders"],
        drug_class="fluoroquinolone"
    ),

    # Anticoagulants
    "warfarin": DrugInfo(
        name="Warfarin",
        max_daily_dose=10,  # Usual max, INR dependent
        unit="mg",
        hepatic_caution=True,
        contraindicated_conditions=["active bleeding", "pregnancy"],
        drug_class="anticoagulant"
    ),
    "rivaroxaban": DrugInfo(
        name="Rivaroxaban",
        max_daily_dose=20,
        unit="mg",
        renal_adjustment_egfr=50,
        contraindicated_conditions=["active bleeding"],
        drug_class="doac"
    ),
}

# Drug-drug interaction database
DRUG_INTERACTIONS: List[Dict[str, Any]] = [
    {
        "drugs": ["warfarin", "aspirin"],
        "severity": "HIGH",
        "message": "Increased bleeding risk with concurrent use",
        "action": "WARN"
    },
    {
        "drugs": ["clopidogrel", "omeprazole"],
        "severity": "MEDIUM",
        "message": "Omeprazole may reduce clopidogrel efficacy. Consider pantoprazole instead.",
        "action": "WARN"
    },
    {
        "drugs": ["metformin", "ibuprofen"],
        "severity": "MEDIUM",
        "message": "NSAIDs may worsen renal function and affect metformin clearance",
        "action": "WARN"
    },
    {
        "drugs": ["ramipril", "potassium"],
        "severity": "HIGH",
        "message": "Risk of hyperkalemia with ACE inhibitor and potassium supplements",
        "action": "WARN"
    },
    {
        "drugs": ["ciprofloxacin", "antacid"],
        "severity": "MEDIUM",
        "message": "Antacids reduce ciprofloxacin absorption. Give 2 hours apart.",
        "action": "WARN"
    },
    {
        "drugs": ["statin", "macrolide"],
        "severity": "HIGH",
        "message": "Increased risk of myopathy/rhabdomyolysis",
        "action": "WARN"
    },
]

# Allergy cross-reactivity
ALLERGY_CROSS_REACTIVITY: Dict[str, List[str]] = {
    "penicillin": ["amoxicillin", "ampicillin", "piperacillin", "cephalosporin"],
    "sulfa": ["sulfamethoxazole", "sulfasalazine", "furosemide", "thiazide"],
    "aspirin": ["ibuprofen", "naproxen", "diclofenac"],  # NSAID cross-reactivity
    "cephalosporin": ["cefixime", "ceftriaxone", "cefuroxime"],
}


class PrescriptionSafetyChecker:
    """
    Validates prescriptions for safety issues.

    This checker uses hard-coded rules and should NEVER be overridden by LLM.
    """

    def __init__(self, db_service=None):
        """
        Initialize the safety checker.

        Args:
            db_service: Optional database service for patient data lookup
        """
        self.db = db_service

    def validate_prescription(
        self,
        prescription: Prescription,
        patient_snapshot: PatientSnapshot
    ) -> List[SafetyAlert]:
        """
        Validate a prescription against safety rules.

        Args:
            prescription: The prescription to validate
            patient_snapshot: Patient's current clinical snapshot

        Returns:
            List of SafetyAlert objects
        """
        alerts = []

        for medication in prescription.medications:
            # 1. Allergy check (CRITICAL - never bypass)
            allergy_alert = self._check_allergy(medication, patient_snapshot.allergies)
            if allergy_alert:
                alerts.append(allergy_alert)

            # 2. Dose limits
            dose_alerts = self._check_dose_limits(medication)
            alerts.extend(dose_alerts)

            # 3. Renal adjustment
            renal_alert = self._check_renal_adjustment(medication, patient_snapshot.key_labs)
            if renal_alert:
                alerts.append(renal_alert)

            # 4. Hepatic caution
            hepatic_alert = self._check_hepatic_caution(medication, patient_snapshot.key_labs)
            if hepatic_alert:
                alerts.append(hepatic_alert)

            # 5. Contraindicated conditions
            condition_alerts = self._check_contraindications(
                medication, patient_snapshot.active_problems
            )
            alerts.extend(condition_alerts)

        # 6. Drug-drug interactions
        interaction_alerts = self._check_interactions(
            prescription.medications,
            patient_snapshot.current_medications
        )
        alerts.extend(interaction_alerts)

        # 7. Duplicate therapy
        duplicate_alerts = self._check_duplicates(
            prescription.medications,
            patient_snapshot.current_medications
        )
        alerts.extend(duplicate_alerts)

        return alerts

    def _check_allergy(
        self,
        medication: Medication,
        allergies: List[str]
    ) -> Optional[SafetyAlert]:
        """Check if medication triggers an allergy."""
        drug_lower = medication.drug_name.lower()

        for allergy in allergies:
            allergy_lower = allergy.lower()

            # Direct match
            if allergy_lower in drug_lower or drug_lower in allergy_lower:
                return SafetyAlert(
                    severity="CRITICAL",
                    category="allergy",
                    message=f"🚫 BLOCKED: {medication.drug_name} - Patient allergic to {allergy}",
                    action="BLOCK",
                    details="Direct allergy match. Do not prescribe."
                )

            # Cross-reactivity check
            for allergen, cross_reactive in ALLERGY_CROSS_REACTIVITY.items():
                if allergen in allergy_lower:
                    for cross_drug in cross_reactive:
                        if cross_drug in drug_lower:
                            return SafetyAlert(
                                severity="CRITICAL",
                                category="allergy",
                                message=f"🚫 BLOCKED: {medication.drug_name} - Cross-reactive with {allergy}",
                                action="BLOCK",
                                details=f"{allergy} allergy has cross-reactivity with {medication.drug_name}"
                            )

        return None

    def _check_dose_limits(self, medication: Medication) -> List[SafetyAlert]:
        """Check if dose exceeds safe limits."""
        alerts = []
        drug_lower = medication.drug_name.lower()

        # Find drug in database
        drug_info = None
        for key, info in DRUG_DATABASE.items():
            if key in drug_lower or drug_lower in key:
                drug_info = info
                break

        if not drug_info:
            return alerts

        # Parse dose and frequency to calculate daily dose
        try:
            daily_dose = self._calculate_daily_dose(medication)

            if drug_info.max_daily_dose and daily_dose > drug_info.max_daily_dose:
                alerts.append(SafetyAlert(
                    severity="HIGH",
                    category="dose",
                    message=f"⚠️ {medication.drug_name}: Daily dose {daily_dose}{drug_info.unit} exceeds max {drug_info.max_daily_dose}{drug_info.unit}",
                    action="WARN",
                    details=f"Prescribed: {medication.dose} {medication.frequency}. Max daily: {drug_info.max_daily_dose}{drug_info.unit}"
                ))

            if drug_info.max_single_dose:
                single_dose = self._parse_dose(medication.dose, medication.strength)
                if single_dose > drug_info.max_single_dose:
                    alerts.append(SafetyAlert(
                        severity="HIGH",
                        category="dose",
                        message=f"⚠️ {medication.drug_name}: Single dose {single_dose}{drug_info.unit} exceeds max {drug_info.max_single_dose}{drug_info.unit}",
                        action="WARN",
                        details=f"Max single dose: {drug_info.max_single_dose}{drug_info.unit}"
                    ))

        except (ValueError, TypeError):
            pass  # Unable to parse dose

        return alerts

    def _check_renal_adjustment(
        self,
        medication: Medication,
        key_labs: Dict[str, Any]
    ) -> Optional[SafetyAlert]:
        """Check if dose adjustment needed for renal function."""
        drug_lower = medication.drug_name.lower()

        # Find drug in database
        drug_info = None
        for key, info in DRUG_DATABASE.items():
            if key in drug_lower:
                drug_info = info
                break

        if not drug_info or not drug_info.renal_adjustment_egfr:
            return None

        # Get eGFR or creatinine
        egfr = None
        if 'egfr' in key_labs:
            try:
                egfr = float(key_labs['egfr'].get('value', 0))
            except (ValueError, TypeError, AttributeError):
                pass

        # Estimate from creatinine if eGFR not available
        if egfr is None and 'creatinine' in key_labs:
            try:
                cr = float(key_labs['creatinine'].get('value', 0))
                if cr > 1.5:  # Rough indicator of impairment
                    return SafetyAlert(
                        severity="MEDIUM",
                        category="renal",
                        message=f"⚠️ {medication.drug_name}: Check dose - Creatinine {cr} mg/dL",
                        action="WARN",
                        details=f"Consider dose adjustment for elevated creatinine"
                    )
            except (ValueError, TypeError, AttributeError):
                pass

        if egfr is not None and egfr < drug_info.renal_adjustment_egfr:
            return SafetyAlert(
                severity="HIGH",
                category="renal",
                message=f"⚠️ {medication.drug_name}: Dose adjustment needed - eGFR {egfr} ml/min",
                action="WARN",
                details=f"Reduce dose or avoid if eGFR < {drug_info.renal_adjustment_egfr}"
            )

        return None

    def _check_hepatic_caution(
        self,
        medication: Medication,
        key_labs: Dict[str, Any]
    ) -> Optional[SafetyAlert]:
        """Check for hepatic impairment concerns."""
        drug_lower = medication.drug_name.lower()

        # Find drug in database
        drug_info = None
        for key, info in DRUG_DATABASE.items():
            if key in drug_lower:
                drug_info = info
                break

        if not drug_info or not drug_info.hepatic_caution:
            return None

        # Check liver enzymes
        for enzyme in ['alt', 'ast', 'sgpt', 'sgot']:
            if enzyme in key_labs:
                try:
                    value = float(key_labs[enzyme].get('value', 0))
                    if value > 80:  # Roughly 2x upper limit
                        return SafetyAlert(
                            severity="MEDIUM",
                            category="hepatic",
                            message=f"⚠️ {medication.drug_name}: Use with caution - Elevated liver enzymes",
                            action="WARN",
                            details=f"{enzyme.upper()}: {value} U/L"
                        )
                except (ValueError, TypeError, AttributeError):
                    pass

        return None

    def _check_contraindications(
        self,
        medication: Medication,
        active_problems: List[str]
    ) -> List[SafetyAlert]:
        """Check for contraindicated conditions."""
        alerts = []
        drug_lower = medication.drug_name.lower()

        # Find drug in database
        drug_info = None
        for key, info in DRUG_DATABASE.items():
            if key in drug_lower:
                drug_info = info
                break

        if not drug_info or not drug_info.contraindicated_conditions:
            return alerts

        for condition in drug_info.contraindicated_conditions:
            for problem in active_problems:
                if condition.lower() in problem.lower():
                    alerts.append(SafetyAlert(
                        severity="HIGH",
                        category="contraindication",
                        message=f"⚠️ {medication.drug_name}: Contraindicated in {condition}",
                        action="WARN",
                        details=f"Patient has: {problem}"
                    ))

        return alerts

    def _check_interactions(
        self,
        new_meds: List[Medication],
        current_meds: List[Medication]
    ) -> List[SafetyAlert]:
        """Check for drug-drug interactions."""
        alerts = []
        all_meds = new_meds + current_meds

        # Get all drug names
        drug_names = [m.drug_name.lower() for m in all_meds]

        for interaction in DRUG_INTERACTIONS:
            drugs = interaction["drugs"]
            matched_drugs = []

            for drug in drugs:
                for med_name in drug_names:
                    if drug in med_name or med_name in drug:
                        matched_drugs.append(med_name)
                        break

            if len(matched_drugs) >= 2:
                alerts.append(SafetyAlert(
                    severity=interaction["severity"],
                    category="interaction",
                    message=f"⚠️ Drug Interaction: {' + '.join(matched_drugs)}",
                    action=interaction["action"],
                    details=interaction["message"]
                ))

        return alerts

    def _check_duplicates(
        self,
        new_meds: List[Medication],
        current_meds: List[Medication]
    ) -> List[SafetyAlert]:
        """Check for duplicate therapy."""
        alerts = []

        for new_med in new_meds:
            new_lower = new_med.drug_name.lower()

            # Get drug class
            new_class = None
            for key, info in DRUG_DATABASE.items():
                if key in new_lower:
                    new_class = info.drug_class
                    break

            for current_med in current_meds:
                current_lower = current_med.drug_name.lower()

                # Same drug
                if new_lower in current_lower or current_lower in new_lower:
                    alerts.append(SafetyAlert(
                        severity="MEDIUM",
                        category="duplicate",
                        message=f"⚠️ Duplicate: {new_med.drug_name} - already on {current_med.drug_name}",
                        action="WARN",
                        details="Verify if this is intentional dose change"
                    ))
                    continue

                # Same class
                if new_class:
                    for key, info in DRUG_DATABASE.items():
                        if key in current_lower and info.drug_class == new_class:
                            alerts.append(SafetyAlert(
                                severity="LOW",
                                category="duplicate",
                                message=f"ℹ️ Same class: {new_med.drug_name} and {current_med.drug_name} are both {new_class}",
                                action="INFO",
                                details="Consider if duplicate therapy is intended"
                            ))

        return alerts

    def _calculate_daily_dose(self, medication: Medication) -> float:
        """Calculate total daily dose from medication."""
        single_dose = self._parse_dose(medication.dose, medication.strength)

        frequency_multiplier = {
            'od': 1, 'qd': 1, 'once daily': 1,
            'bd': 2, 'bid': 2, 'twice daily': 2,
            'tds': 3, 'tid': 3, 'thrice daily': 3,
            'qid': 4, 'four times': 4,
            'hs': 1, 'at bedtime': 1,
            'sos': 0.5, 'prn': 0.5, 'as needed': 0.5,
            'stat': 1,
        }

        freq_lower = medication.frequency.lower()
        multiplier = frequency_multiplier.get(freq_lower, 1)

        return single_dose * multiplier

    def _parse_dose(self, dose: str, strength: str) -> float:
        """Parse dose value from dose and strength strings."""
        # Try to extract number from dose
        dose_match = re.search(r'(\d+(?:\.\d+)?)', dose)
        strength_match = re.search(r'(\d+(?:\.\d+)?)', strength)

        dose_num = float(dose_match.group(1)) if dose_match else 1
        strength_num = float(strength_match.group(1)) if strength_match else 0

        if strength_num > 0:
            return dose_num * strength_num
        return dose_num


class CriticalInfoBanner:
    """
    Generates critical information banner that should ALWAYS be visible.

    This information should never be hidden or summarized by AI.
    """

    def __init__(self, db_service=None):
        self.db = db_service

    def get_banner(self, patient_snapshot: PatientSnapshot) -> str:
        """
        Generate critical info banner for a patient.

        Args:
            patient_snapshot: Patient's clinical snapshot

        Returns:
            Formatted banner string
        """
        lines = ["🚨 CRITICAL INFO (Always Visible):"]

        # Allergies (MOST IMPORTANT)
        if patient_snapshot.allergies:
            allergy_str = ", ".join(patient_snapshot.allergies)
            lines.append(f"⚠️ ALLERGIES: {allergy_str}")
        else:
            lines.append("✓ NKDA (No Known Drug Allergies)")

        # Blood group
        if patient_snapshot.blood_group:
            lines.append(f"🩸 Blood Group: {patient_snapshot.blood_group}")

        # Code status
        if patient_snapshot.code_status != "FULL":
            lines.append(f"📋 CODE STATUS: {patient_snapshot.code_status}")

        # Anticoagulation
        if patient_snapshot.on_anticoagulation:
            lines.append(f"💉 ON ANTICOAGULATION: {patient_snapshot.anticoag_drug or 'Unknown'}")

        return "\n".join(lines)

    def get_banner_dict(self, patient_snapshot: PatientSnapshot) -> Dict[str, Any]:
        """Get critical info as dictionary for UI."""
        return {
            "allergies": patient_snapshot.allergies or [],
            "nkda": len(patient_snapshot.allergies) == 0,
            "blood_group": patient_snapshot.blood_group,
            "code_status": patient_snapshot.code_status,
            "on_anticoagulation": patient_snapshot.on_anticoagulation,
            "anticoag_drug": patient_snapshot.anticoag_drug,
        }
