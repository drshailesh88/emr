"""Smart dosing calculations based on patient parameters"""
from dataclasses import dataclass
from typing import Optional, List, Dict
import math
import json
from pathlib import Path

@dataclass
class DoseRecommendation:
    drug: str
    recommended_dose: str
    original_dose: Optional[str]
    adjustment_reason: str
    adjustment_type: str  # renal, hepatic, pediatric, geriatric
    confidence: float  # 0.0 to 1.0
    warnings: List[str]
    references: List[str]

class DoseCalculator:
    """Calculate adjusted doses based on patient parameters"""

    def __init__(self, dosing_data_path: str = "data/dosing"):
        self.dosing_db: Dict = {}
        self.renal_adjustments: Dict = {}
        self.hepatic_adjustments: Dict = {}
        self.pediatric_doses: Dict = {}
        self._load_dosing_data(dosing_data_path)

    def _load_dosing_data(self, path: str):
        """Load dosing adjustment data"""
        try:
            # Load renal adjustments
            renal_file = Path(path) / "renal_adjustments.json"
            if renal_file.exists():
                with open(renal_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.renal_adjustments = data.get('adjustments', {})

            # Load hepatic adjustments
            hepatic_file = Path(path) / "hepatic_adjustments.json"
            if hepatic_file.exists():
                with open(hepatic_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.hepatic_adjustments = data.get('adjustments', {})

            # Load pediatric doses
            pediatric_file = Path(path) / "pediatric_doses.json"
            if pediatric_file.exists():
                with open(pediatric_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.pediatric_doses = data.get('doses', {})

            print(f"Loaded dosing adjustments")

        except Exception as e:
            print(f"Error loading dosing data: {e}")
            self._create_sample_dosing_data()

    def _create_sample_dosing_data(self):
        """Create sample dosing data"""
        # Sample renal adjustments
        self.renal_adjustments = {
            'metformin': {
                'egfr_thresholds': [
                    {'min': 45, 'max': 999, 'adjustment': '100%', 'note': 'No adjustment needed'},
                    {'min': 30, 'max': 45, 'adjustment': '50%', 'note': 'Reduce dose by 50%'},
                    {'min': 0, 'max': 30, 'adjustment': 'contraindicated', 'note': 'Risk of lactic acidosis'}
                ]
            },
            'gabapentin': {
                'egfr_thresholds': [
                    {'min': 60, 'max': 999, 'adjustment': '100%', 'note': 'No adjustment'},
                    {'min': 30, 'max': 59, 'adjustment': '50%', 'note': 'Reduce by 50%'},
                    {'min': 15, 'max': 29, 'adjustment': '25%', 'note': 'Reduce by 75%'},
                    {'min': 0, 'max': 14, 'adjustment': '10%', 'note': 'Reduce by 90%'}
                ]
            }
        }

        # Sample pediatric doses
        self.pediatric_doses = {
            'paracetamol': {
                'dose_per_kg': 15,  # mg/kg/dose
                'max_dose_per_kg': 75,  # mg/kg/day
                'max_single_dose': 1000,  # mg
                'max_daily_dose': 4000,  # mg
                'frequency': 'Q6H PRN'
            },
            'amoxicillin': {
                'dose_per_kg': 20,  # mg/kg/dose
                'max_dose_per_kg': 90,  # mg/kg/day
                'max_daily_dose': 3000,  # mg
                'frequency': 'TDS'
            }
        }

    def calculate_egfr(self,
                      creatinine: float,
                      age: int,
                      gender: str,
                      weight: Optional[float] = None,
                      race: Optional[str] = None) -> float:
        """
        Calculate eGFR using CKD-EPI 2021 equation (race-free).

        Args:
            creatinine: Serum creatinine in mg/dL
            age: Age in years
            gender: 'M' or 'F'
            weight: Weight in kg (optional, for Cockcroft-Gault)

        Returns:
            eGFR in mL/min/1.73m²
        """
        # CKD-EPI 2021 (race-free)
        kappa = 0.7 if gender.upper() == 'F' else 0.9
        alpha = -0.241 if gender.upper() == 'F' else -0.302
        gender_factor = 1.012 if gender.upper() == 'F' else 1.0

        scr_kappa = creatinine / kappa
        min_term = min(scr_kappa, 1.0)
        max_term = max(scr_kappa, 1.0)

        egfr = 142 * (min_term ** alpha) * (max_term ** -1.200) * (0.9938 ** age) * gender_factor

        return round(egfr, 1)

    def calculate_creatinine_clearance(self,
                                       creatinine: float,
                                       age: int,
                                       weight: float,
                                       gender: str) -> float:
        """Calculate CrCl using Cockcroft-Gault equation"""
        # Cockcroft-Gault: CrCl = ((140 - age) × weight) / (72 × SCr) [× 0.85 if female]
        crcl = ((140 - age) * weight) / (72 * creatinine)

        if gender.upper() == 'F':
            crcl *= 0.85

        return round(crcl, 1)

    def calculate_renal_dose(self,
                            drug: str,
                            egfr: float,
                            original_dose: Optional[str] = None) -> Optional[DoseRecommendation]:
        """Adjust dose for renal impairment"""
        drug_lower = drug.lower()

        if drug_lower not in self.renal_adjustments:
            return None

        adjustment_data = self.renal_adjustments[drug_lower]
        thresholds = adjustment_data.get('egfr_thresholds', [])

        for threshold in thresholds:
            if threshold['min'] <= egfr < threshold['max']:
                adjustment = threshold['adjustment']
                note = threshold['note']

                if adjustment == 'contraindicated':
                    return DoseRecommendation(
                        drug=drug,
                        recommended_dose="CONTRAINDICATED",
                        original_dose=original_dose,
                        adjustment_reason=f"eGFR {egfr} mL/min/1.73m² - {note}",
                        adjustment_type="renal",
                        confidence=1.0,
                        warnings=[f"Do not use {drug} with eGFR < {threshold['max']}"],
                        references=["Renal dosing guidelines"]
                    )

                recommended_dose = original_dose if original_dose else f"{adjustment} of standard dose"

                return DoseRecommendation(
                    drug=drug,
                    recommended_dose=recommended_dose,
                    original_dose=original_dose,
                    adjustment_reason=f"eGFR {egfr} mL/min/1.73m² - {note}",
                    adjustment_type="renal",
                    confidence=0.9,
                    warnings=[note],
                    references=["Renal dosing guidelines"]
                )

        return None

    def calculate_hepatic_dose(self,
                              drug: str,
                              child_pugh_score: str,  # A, B, or C
                              original_dose: Optional[str] = None) -> Optional[DoseRecommendation]:
        """Adjust dose for hepatic impairment"""
        drug_lower = drug.lower()

        if drug_lower not in self.hepatic_adjustments:
            return None

        adjustment_data = self.hepatic_adjustments[drug_lower]
        adjustment = adjustment_data.get(f'child_pugh_{child_pugh_score.upper()}', {})

        if not adjustment:
            return None

        return DoseRecommendation(
            drug=drug,
            recommended_dose=adjustment.get('dose', original_dose),
            original_dose=original_dose,
            adjustment_reason=f"Child-Pugh {child_pugh_score.upper()} - {adjustment.get('note', '')}",
            adjustment_type="hepatic",
            confidence=0.8,
            warnings=adjustment.get('warnings', []),
            references=["Hepatic dosing guidelines"]
        )

    def calculate_pediatric_dose(self,
                                drug: str,
                                weight_kg: float,
                                age_years: float,
                                indication: Optional[str] = None) -> Optional[DoseRecommendation]:
        """Calculate weight-based pediatric dose"""
        drug_lower = drug.lower()

        if drug_lower not in self.pediatric_doses:
            return None

        dose_data = self.pediatric_doses[drug_lower]
        dose_per_kg = dose_data['dose_per_kg']
        max_dose_per_kg = dose_data.get('max_dose_per_kg', 999)
        max_single_dose = dose_data.get('max_single_dose', 99999)
        max_daily_dose = dose_data.get('max_daily_dose', 99999)
        frequency = dose_data.get('frequency', 'TDS')

        # Calculate dose
        calculated_dose = dose_per_kg * weight_kg
        calculated_dose = min(calculated_dose, max_single_dose)

        # Calculate daily dose based on frequency
        freq_multipliers = {
            'OD': 1, 'BD': 2, 'TDS': 3, 'QID': 4,
            'Q6H': 4, 'Q8H': 3, 'Q12H': 2
        }
        daily_multiplier = freq_multipliers.get(frequency.split()[0], 3)
        daily_dose = calculated_dose * daily_multiplier

        warnings = []
        if daily_dose > max_daily_dose:
            warnings.append(f"Calculated daily dose exceeds maximum ({max_daily_dose}mg/day)")
            calculated_dose = max_daily_dose / daily_multiplier

        return DoseRecommendation(
            drug=drug,
            recommended_dose=f"{calculated_dose:.0f}mg {frequency}",
            original_dose=None,
            adjustment_reason=f"Weight-based dosing: {dose_per_kg}mg/kg × {weight_kg}kg",
            adjustment_type="pediatric",
            confidence=0.95,
            warnings=warnings,
            references=["Pediatric dosing guidelines"]
        )

    def calculate_geriatric_dose(self,
                                drug: str,
                                age: int,
                                egfr: Optional[float] = None) -> Optional[DoseRecommendation]:
        """Adjust dose for elderly patients"""
        if age < 65:
            return None

        warnings = []

        # Many drugs require dose reduction in elderly
        geriatric_sensitive_drugs = {
            'digoxin': {'reduction': '50%', 'note': 'Start low, go slow'},
            'opioids': {'reduction': '50%', 'note': 'Increased sensitivity in elderly'},
            'benzodiazepines': {'reduction': '50%', 'note': 'Fall risk, cognitive impairment'},
        }

        drug_lower = drug.lower()
        if drug_lower in geriatric_sensitive_drugs:
            data = geriatric_sensitive_drugs[drug_lower]
            warnings.append(data['note'])

            return DoseRecommendation(
                drug=drug,
                recommended_dose=data['reduction'] + " of standard dose",
                original_dose=None,
                adjustment_reason=f"Age {age} years - {data['note']}",
                adjustment_type="geriatric",
                confidence=0.8,
                warnings=warnings,
                references=["Geriatric dosing guidelines", "Beers Criteria"]
            )

        # Also check for renal adjustment if eGFR provided
        if egfr:
            renal_rec = self.calculate_renal_dose(drug, egfr)
            if renal_rec:
                renal_rec.warnings.append("Consider geriatric sensitivity")
                return renal_rec

        return None

    def get_ckd_stage(self, egfr: float) -> str:
        """Get CKD stage from eGFR"""
        if egfr >= 90:
            return "G1 (Normal)"
        elif egfr >= 60:
            return "G2 (Mild)"
        elif egfr >= 45:
            return "G3a (Mild-moderate)"
        elif egfr >= 30:
            return "G3b (Moderate-severe)"
        elif egfr >= 15:
            return "G4 (Severe)"
        else:
            return "G5 (Kidney failure)"
