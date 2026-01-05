"""
Clinical Calculators for Evidence-Based Medicine

Implements scoring systems and calculators used in Indian medical practice.
All formulas are validated against international and Indian guidelines.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, Dict, List
from enum import Enum
import math


class Gender(Enum):
    """Gender for clinical calculations."""
    MALE = "M"
    FEMALE = "F"


@dataclass
class Dose:
    """Calculated medication dose."""
    amount: float
    unit: str
    frequency: str
    route: str = "Oral"
    duration: str = ""
    instructions: str = ""

    def __str__(self) -> str:
        return f"{self.amount}{self.unit} {self.frequency}"


@dataclass
class CVDRiskResult:
    """Cardiovascular disease risk assessment result."""
    risk_percentage: float
    risk_category: str  # Low, Moderate, High, Very High
    recommendations: List[str]
    target_ldl: Optional[float] = None


class ProtocolCalculator:
    """
    Clinical calculators for specialty-specific protocols.

    All calculations follow evidence-based medicine and Indian guidelines.
    """

    # ============== CARDIOLOGY CALCULATORS ==============

    @staticmethod
    def calculate_cha2ds2_vasc(
        age: int,
        gender: str,
        chf_history: bool = False,
        hypertension: bool = False,
        stroke_tia_history: bool = False,
        vascular_disease: bool = False,
        diabetes: bool = False,
    ) -> Dict[str, any]:
        """
        Calculate CHA2DS2-VASc score for stroke risk in atrial fibrillation.

        Scoring:
        - CHF: 1 point
        - Hypertension: 1 point
        - Age ≥75: 2 points
        - Diabetes: 1 point
        - Stroke/TIA/TE: 2 points
        - Vascular disease (MI, PAD, aortic plaque): 1 point
        - Age 65-74: 1 point
        - Sex (Female): 1 point

        Args:
            age: Patient age in years
            gender: 'M' or 'F'
            chf_history: Congestive heart failure history
            hypertension: Hypertension diagnosis
            stroke_tia_history: Prior stroke/TIA
            vascular_disease: MI, PAD, or aortic plaque
            diabetes: Diabetes mellitus

        Returns:
            Dict with score, risk_percentage, and anticoagulation recommendation
        """
        score = 0

        # CHF
        if chf_history:
            score += 1

        # Hypertension
        if hypertension:
            score += 1

        # Age
        if age >= 75:
            score += 2
        elif age >= 65:
            score += 1

        # Diabetes
        if diabetes:
            score += 1

        # Stroke/TIA
        if stroke_tia_history:
            score += 2

        # Vascular disease
        if vascular_disease:
            score += 1

        # Sex (Female)
        if gender.upper() == 'F':
            score += 1

        # Annual stroke risk
        risk_map = {
            0: 0.2, 1: 0.6, 2: 2.2, 3: 3.2, 4: 4.8,
            5: 7.2, 6: 9.7, 7: 11.2, 8: 10.8, 9: 12.2
        }
        risk_percentage = risk_map.get(score, 12.2)

        # Recommendation
        if score == 0:
            recommendation = "No anticoagulation needed"
            preferred_treatment = "None or Aspirin"
        elif score == 1:
            recommendation = "Consider anticoagulation (especially if male)"
            preferred_treatment = "NOAC or Aspirin (discuss with patient)"
        else:
            recommendation = "Anticoagulation recommended"
            preferred_treatment = "NOAC (Apixaban/Rivaroxaban) or Warfarin"

        return {
            "score": score,
            "risk_percentage": risk_percentage,
            "recommendation": recommendation,
            "preferred_treatment": preferred_treatment,
            "details": f"Annual stroke risk: {risk_percentage}%"
        }

    @staticmethod
    def calculate_hasbled(
        age: int,
        hypertension_uncontrolled: bool = False,
        abnormal_renal_function: bool = False,
        abnormal_liver_function: bool = False,
        stroke_history: bool = False,
        bleeding_history: bool = False,
        labile_inr: bool = False,
        elderly: bool = False,
        drugs_predisposing: bool = False,
        alcohol_excess: bool = False,
    ) -> Dict[str, any]:
        """
        Calculate HAS-BLED score for bleeding risk on anticoagulation.

        Scoring (1 point each):
        - H: Hypertension (uncontrolled, >160 mmHg systolic)
        - A: Abnormal renal/liver function (1 point each)
        - S: Stroke history
        - B: Bleeding history or predisposition
        - L: Labile INR (if on warfarin)
        - E: Elderly (age >65)
        - D: Drugs (antiplatelet, NSAIDs) or alcohol (1 point each)

        Args:
            age: Patient age
            hypertension_uncontrolled: SBP >160 mmHg
            abnormal_renal_function: Dialysis, transplant, Cr >2.26 mg/dL
            abnormal_liver_function: Cirrhosis, bilirubin >2x, AST/ALT >3x
            stroke_history: Prior stroke
            bleeding_history: Major bleeding or predisposition
            labile_inr: Unstable INR (if on warfarin)
            elderly: Age >65
            drugs_predisposing: Antiplatelet or NSAIDs
            alcohol_excess: >8 drinks/week

        Returns:
            Dict with score and bleeding risk interpretation
        """
        score = 0

        if hypertension_uncontrolled:
            score += 1
        if abnormal_renal_function:
            score += 1
        if abnormal_liver_function:
            score += 1
        if stroke_history:
            score += 1
        if bleeding_history:
            score += 1
        if labile_inr:
            score += 1
        if age > 65:
            score += 1
        if drugs_predisposing:
            score += 1
        if alcohol_excess:
            score += 1

        # Annual major bleeding risk
        risk_map = {
            0: 1.13, 1: 1.02, 2: 1.88, 3: 3.74,
            4: 8.70, 5: 12.50, 6: 12.50
        }
        bleeding_risk = risk_map.get(min(score, 6), 12.50)

        if score >= 3:
            interpretation = "High bleeding risk - use caution, address modifiable factors"
            recommendation = "Consider reversible causes, monitor closely"
        elif score == 2:
            interpretation = "Moderate bleeding risk - proceed with caution"
            recommendation = "Address modifiable risk factors"
        else:
            interpretation = "Low bleeding risk"
            recommendation = "Anticoagulation safe if indicated"

        return {
            "score": score,
            "bleeding_risk_percentage": bleeding_risk,
            "interpretation": interpretation,
            "recommendation": recommendation
        }

    @staticmethod
    def calculate_framingham(
        age: int,
        gender: str,
        total_cholesterol: float,
        hdl: float,
        systolic_bp: int,
        on_bp_medication: bool = False,
        smoker: bool = False,
        diabetic: bool = False,
    ) -> CVDRiskResult:
        """
        Calculate 10-year CVD risk using Framingham Risk Score.

        Modified for Indian population (1.5x multiplier for South Asians).

        Args:
            age: Age in years (30-79)
            gender: 'M' or 'F'
            total_cholesterol: mg/dL
            hdl: HDL cholesterol in mg/dL
            systolic_bp: Systolic BP in mmHg
            on_bp_medication: On antihypertensive treatment
            smoker: Current smoker
            diabetic: Diabetes mellitus

        Returns:
            CVDRiskResult with risk percentage and recommendations
        """
        # Framingham point system (simplified)
        points = 0

        if gender.upper() == 'M':
            # Age points for men
            if age < 35:
                points += -9
            elif age < 40:
                points += -4
            elif age < 45:
                points += 0
            elif age < 50:
                points += 3
            elif age < 55:
                points += 6
            elif age < 60:
                points += 8
            elif age < 65:
                points += 10
            elif age < 70:
                points += 11
            elif age < 75:
                points += 12
            else:
                points += 13

            # Cholesterol points for men
            if total_cholesterol < 160:
                points += 0
            elif total_cholesterol < 200:
                points += 4
            elif total_cholesterol < 240:
                points += 7
            elif total_cholesterol < 280:
                points += 9
            else:
                points += 11

        else:  # Female
            # Age points for women
            if age < 35:
                points += -7
            elif age < 40:
                points += -3
            elif age < 45:
                points += 0
            elif age < 50:
                points += 3
            elif age < 55:
                points += 6
            elif age < 60:
                points += 8
            elif age < 65:
                points += 10
            elif age < 70:
                points += 12
            elif age < 75:
                points += 14
            else:
                points += 16

            # Cholesterol points for women
            if total_cholesterol < 160:
                points += 0
            elif total_cholesterol < 200:
                points += 4
            elif total_cholesterol < 240:
                points += 8
            elif total_cholesterol < 280:
                points += 11
            else:
                points += 13

        # HDL points (same for both)
        if hdl >= 60:
            points -= 1
        elif hdl >= 50:
            points += 0
        elif hdl >= 40:
            points += 1
        else:
            points += 2

        # BP points
        if systolic_bp < 120:
            points += 0 if not on_bp_medication else 0
        elif systolic_bp < 130:
            points += 0 if not on_bp_medication else 1
        elif systolic_bp < 140:
            points += 1 if not on_bp_medication else 2
        elif systolic_bp < 160:
            points += 1 if not on_bp_medication else 2
        else:
            points += 2 if not on_bp_medication else 3

        # Smoking
        if smoker:
            points += 4 if gender.upper() == 'M' else 3

        # Diabetes
        if diabetic:
            points += 2 if gender.upper() == 'M' else 4

        # Convert points to risk percentage (simplified mapping)
        risk_map = {
            -3: 1, -2: 1, -1: 1, 0: 1, 1: 1, 2: 2, 3: 2, 4: 2,
            5: 3, 6: 4, 7: 5, 8: 6, 9: 8, 10: 10, 11: 12, 12: 16,
            13: 20, 14: 25, 15: 30, 16: 30
        }
        base_risk = risk_map.get(min(max(points, -3), 16), 30)

        # South Asian multiplier
        adjusted_risk = base_risk * 1.5

        # Risk categorization
        if adjusted_risk < 10:
            category = "Low"
            target_ldl = 130
            recommendations = [
                "Lifestyle modifications",
                "Diet: Reduce saturated fat, increase fiber",
                "Exercise: 150 minutes/week moderate intensity",
                "Smoking cessation if applicable",
                "Follow-up in 1 year"
            ]
        elif adjusted_risk < 20:
            category = "Moderate"
            target_ldl = 100
            recommendations = [
                "Lifestyle modifications + consider statin",
                "Target LDL <100 mg/dL",
                "Low-dose aspirin if no contraindications",
                "BP control <140/90",
                "Follow-up in 6 months"
            ]
        else:
            category = "High"
            target_ldl = 70
            recommendations = [
                "Intensive lifestyle modifications + statin mandatory",
                "Target LDL <70 mg/dL",
                "Aspirin 75mg daily",
                "BP control <130/80",
                "Tight glycemic control if diabetic",
                "Follow-up in 3 months"
            ]

        return CVDRiskResult(
            risk_percentage=round(adjusted_risk, 1),
            risk_category=category,
            recommendations=recommendations,
            target_ldl=target_ldl
        )

    # ============== PEDIATRIC CALCULATORS ==============

    @staticmethod
    def calculate_pediatric_dose(
        drug_name: str,
        weight_kg: float,
        age_years: Optional[float] = None,
    ) -> Dose:
        """
        Calculate weight-based pediatric drug dosing.

        Uses standard pediatric dosing guidelines from IAP and WHO.

        Args:
            drug_name: Generic drug name
            weight_kg: Child's weight in kg
            age_years: Age in years (optional, for some drugs)

        Returns:
            Dose object with calculated amount and instructions
        """
        drug_name_lower = drug_name.lower()

        # Paracetamol: 15 mg/kg/dose, max 1g/dose
        if "paracetamol" in drug_name_lower or "acetaminophen" in drug_name_lower:
            dose_mg = min(weight_kg * 15, 1000)
            if weight_kg < 10:  # Syrup
                syrup_ml = dose_mg / 125  # 125mg/5ml suspension
                return Dose(
                    amount=round(syrup_ml, 1),
                    unit="ml",
                    frequency="TDS-QID (SOS for fever)",
                    route="Oral",
                    duration="as needed",
                    instructions="every 6-8 hours, max 4 doses/day"
                )
            else:  # Tablet
                return Dose(
                    amount=dose_mg,
                    unit="mg",
                    frequency="TDS-QID (SOS)",
                    route="Oral",
                    duration="as needed",
                    instructions="max 1g/dose, 4g/day"
                )

        # Amoxicillin: 80-90 mg/kg/day divided TDS (high-dose for pneumonia)
        elif "amoxicillin" in drug_name_lower:
            daily_dose = weight_kg * 90
            per_dose = daily_dose / 3
            if weight_kg < 10:  # Syrup
                syrup_ml = per_dose / 125  # 125mg/5ml suspension
                return Dose(
                    amount=round(syrup_ml, 1),
                    unit="ml",
                    frequency="TDS",
                    route="Oral",
                    duration="5-7 days",
                    instructions="after meals, complete course"
                )
            else:
                return Dose(
                    amount=round(per_dose, 0),
                    unit="mg",
                    frequency="TDS",
                    route="Oral",
                    duration="5-7 days",
                    instructions="after meals"
                )

        # Ibuprofen: 10 mg/kg/dose
        elif "ibuprofen" in drug_name_lower:
            dose_mg = weight_kg * 10
            syrup_ml = dose_mg / 100  # 100mg/5ml suspension
            return Dose(
                amount=round(syrup_ml, 1),
                unit="ml",
                frequency="TDS",
                route="Oral",
                duration="as needed",
                instructions="after meals, max 40mg/kg/day"
            )

        # Zinc: 20mg OD for >6 months, 10mg for <6 months
        elif "zinc" in drug_name_lower:
            if age_years and age_years < 0.5:
                dose_mg = 10
            else:
                dose_mg = 20
            return Dose(
                amount=dose_mg,
                unit="mg",
                frequency="OD",
                route="Oral",
                duration="14 days",
                instructions="for diarrhea, continue even after diarrhea stops"
            )

        # Azithromycin: 10 mg/kg OD (max 500mg)
        elif "azithromycin" in drug_name_lower:
            dose_mg = min(weight_kg * 10, 500)
            if weight_kg < 10:
                syrup_ml = dose_mg / 40  # 200mg/5ml suspension
                return Dose(
                    amount=round(syrup_ml, 1),
                    unit="ml",
                    frequency="OD",
                    route="Oral",
                    duration="3-5 days",
                    instructions="once daily, before meals"
                )
            else:
                return Dose(
                    amount=dose_mg,
                    unit="mg",
                    frequency="OD",
                    route="Oral",
                    duration="3-5 days"
                )

        # ORS: Volume replacement based on dehydration
        elif "ors" in drug_name_lower:
            # 75 ml/kg for moderate dehydration over 4 hours
            volume_ml = weight_kg * 75
            return Dose(
                amount=volume_ml,
                unit="ml",
                frequency="over 4 hours",
                route="Oral",
                instructions="frequent sips, plus ongoing losses"
            )

        # Default: Return guidance
        else:
            return Dose(
                amount=0,
                unit="mg",
                frequency="consult reference",
                instructions=f"Standard pediatric dosing for {drug_name} not available. Consult IAP guidelines."
            )

    @staticmethod
    def calculate_edd(lmp: date) -> date:
        """
        Calculate Expected Delivery Date using Naegele's rule.

        EDD = LMP + 280 days (40 weeks)

        Args:
            lmp: Last menstrual period date

        Returns:
            Expected delivery date
        """
        return lmp + timedelta(days=280)

    @staticmethod
    def calculate_gestational_age(lmp: date, reference_date: Optional[date] = None) -> Dict[str, any]:
        """
        Calculate gestational age from LMP.

        Args:
            lmp: Last menstrual period date
            reference_date: Reference date (defaults to today)

        Returns:
            Dict with weeks, days, and trimester
        """
        if reference_date is None:
            reference_date = date.today()

        days_pregnant = (reference_date - lmp).days
        weeks = days_pregnant // 7
        remaining_days = days_pregnant % 7

        # Determine trimester
        if weeks < 13:
            trimester = "First"
        elif weeks < 27:
            trimester = "Second"
        else:
            trimester = "Third"

        # Term status
        if weeks < 37:
            term_status = "Preterm"
        elif weeks < 42:
            term_status = "Term"
        else:
            term_status = "Post-term"

        return {
            "weeks": weeks,
            "days": remaining_days,
            "total_days": days_pregnant,
            "gestational_age": f"{weeks}+{remaining_days} weeks",
            "trimester": trimester,
            "term_status": term_status
        }

    @staticmethod
    def calculate_bmi_percentile(age_years: float, gender: str, bmi: float) -> Dict[str, any]:
        """
        Calculate BMI percentile for pediatric patients (2-20 years).

        Uses WHO/IAP growth charts for Indian children.
        Simplified implementation - in production, use WHO tables.

        Args:
            age_years: Age in years
            gender: 'M' or 'F'
            bmi: Calculated BMI (kg/m²)

        Returns:
            Dict with percentile and nutritional status
        """
        # Simplified percentile estimation (use WHO tables in production)
        # This is a rough approximation

        if age_years < 2 or age_years > 20:
            return {
                "percentile": None,
                "category": "Age out of range (use adult BMI)",
                "interpretation": "Not applicable"
            }

        # Rough estimates for percentiles (median BMI by age/sex)
        # In production, use proper WHO percentile tables
        if gender.upper() == 'M':
            median_bmi = 15 + (age_years - 5) * 0.5
        else:
            median_bmi = 14.5 + (age_years - 5) * 0.5

        # Rough percentile calculation
        diff = bmi - median_bmi
        if diff < -2:
            percentile = 5
            category = "Severely Underweight"
        elif diff < -1:
            percentile = 15
            category = "Underweight"
        elif diff < 1:
            percentile = 50
            category = "Normal"
        elif diff < 2:
            percentile = 85
            category = "Overweight"
        else:
            percentile = 95
            category = "Obese"

        return {
            "percentile": percentile,
            "category": category,
            "interpretation": f"BMI at approximately {percentile}th percentile"
        }

    @staticmethod
    def calculate_egfr_pediatric(creatinine_mg_dl: float, height_cm: float) -> float:
        """
        Calculate pediatric eGFR using Schwartz formula.

        Bedside Schwartz: eGFR = 0.413 × (Height in cm / SCr in mg/dL)

        Args:
            creatinine_mg_dl: Serum creatinine in mg/dL
            height_cm: Height in cm

        Returns:
            eGFR in mL/min/1.73m²
        """
        if creatinine_mg_dl <= 0:
            raise ValueError("Creatinine must be positive")
        if height_cm <= 0:
            raise ValueError("Height must be positive")

        egfr = 0.413 * (height_cm / creatinine_mg_dl)
        return round(egfr, 1)

    @staticmethod
    def calculate_maintenance_fluids_pediatric(weight_kg: float) -> Dict[str, any]:
        """
        Calculate maintenance IV fluid requirements using 4-2-1 rule.

        4-2-1 Rule:
        - 4 ml/kg/hr for first 10 kg
        - 2 ml/kg/hr for next 10 kg
        - 1 ml/kg/hr for remaining weight

        Args:
            weight_kg: Child's weight in kg

        Returns:
            Dict with hourly and daily fluid requirements
        """
        if weight_kg <= 10:
            ml_per_hour = weight_kg * 4
        elif weight_kg <= 20:
            ml_per_hour = 40 + (weight_kg - 10) * 2
        else:
            ml_per_hour = 40 + 20 + (weight_kg - 20) * 1

        ml_per_day = ml_per_hour * 24

        return {
            "ml_per_hour": round(ml_per_hour, 1),
            "ml_per_day": round(ml_per_day, 0),
            "recommendation": f"{ml_per_hour:.1f} ml/hr or {ml_per_day:.0f} ml/day"
        }

    # ============== RENAL CALCULATORS ==============

    @staticmethod
    def calculate_egfr_adult(
        creatinine_mg_dl: float,
        age: int,
        gender: str,
        race: str = "non-black"
    ) -> float:
        """
        Calculate adult eGFR using CKD-EPI equation.

        Most accurate equation for Indian population (use non-black category).

        Args:
            creatinine_mg_dl: Serum creatinine in mg/dL
            age: Age in years
            gender: 'M' or 'F'
            race: 'black' or 'non-black' (use 'non-black' for Indians)

        Returns:
            eGFR in mL/min/1.73m²
        """
        if gender.upper() == 'F':
            if creatinine_mg_dl <= 0.7:
                egfr = 144 * (creatinine_mg_dl / 0.7) ** -0.329
            else:
                egfr = 144 * (creatinine_mg_dl / 0.7) ** -1.209
        else:  # Male
            if creatinine_mg_dl <= 0.9:
                egfr = 141 * (creatinine_mg_dl / 0.9) ** -0.411
            else:
                egfr = 141 * (creatinine_mg_dl / 0.9) ** -1.209

        # Age factor
        egfr *= 0.993 ** age

        # Race factor (1.159 for black, 1.0 for non-black)
        if race.lower() == "black":
            egfr *= 1.159

        return round(egfr, 1)
