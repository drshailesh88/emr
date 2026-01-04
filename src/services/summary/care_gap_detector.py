"""Detect gaps in patient care based on clinical guidelines."""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import date, timedelta
from enum import Enum


class GapSeverity(Enum):
    """Severity of care gap."""
    OVERDUE = "overdue"          # Past due date
    DUE_SOON = "due_soon"        # Due within 30 days
    RECOMMENDED = "recommended"  # Good practice but not urgent


@dataclass
class CareGap:
    """Represents a gap in patient care."""
    care_type: str
    description: str
    last_performed: Optional[date]
    due_date: date
    days_overdue: int
    severity: GapSeverity
    recommendation: str
    applies_to: List[str]
    priority: int = 0  # Higher = more urgent


class CareGapDetector:
    """Detect gaps in preventive and chronic disease care."""

    # Diabetes care monitoring schedule
    DIABETES_CARE = {
        "hba1c": {
            "description": "HbA1c monitoring",
            "frequency_months": 3,
            "recommendation": "Order HbA1c to assess glycemic control",
            "priority": 3,
        },
        "eye_exam": {
            "description": "Diabetic retinopathy screening",
            "frequency_months": 12,
            "recommendation": "Refer to ophthalmology for dilated fundus exam",
            "priority": 2,
        },
        "foot_exam": {
            "description": "Diabetic foot examination",
            "frequency_months": 12,
            "recommendation": "Perform monofilament test and pedal pulse check",
            "priority": 2,
        },
        "urine_acr": {
            "description": "Urine albumin-creatinine ratio",
            "frequency_months": 12,
            "recommendation": "Order spot urine ACR to screen for nephropathy",
            "priority": 2,
        },
        "lipid_panel": {
            "description": "Lipid panel for diabetes",
            "frequency_months": 12,
            "recommendation": "Order fasting lipid profile",
            "priority": 2,
        },
        "creatinine": {
            "description": "Renal function for diabetes",
            "frequency_months": 12,
            "recommendation": "Check serum creatinine and calculate eGFR",
            "priority": 2,
        },
    }

    # Hypertension care monitoring schedule
    HYPERTENSION_CARE = {
        "bp_check": {
            "description": "Blood pressure monitoring",
            "frequency_months": 3,
            "recommendation": "Check blood pressure at each visit",
            "priority": 3,
        },
        "creatinine": {
            "description": "Renal function for hypertension",
            "frequency_months": 12,
            "recommendation": "Order serum creatinine and eGFR",
            "priority": 2,
        },
        "potassium": {
            "description": "Potassium level",
            "frequency_months": 12,
            "recommendation": "Order serum potassium (especially if on ACE/ARB/diuretic)",
            "priority": 2,
        },
        "lipid_panel": {
            "description": "Lipid panel for cardiovascular risk",
            "frequency_months": 12,
            "recommendation": "Order fasting lipid profile",
            "priority": 2,
        },
    }

    # Coronary artery disease care
    CAD_CARE = {
        "lipid_panel": {
            "description": "Lipid panel for CAD patient",
            "frequency_months": 6,
            "recommendation": "Order lipid panel to ensure LDL at target (<70 for high risk)",
            "priority": 3,
        },
        "echo": {
            "description": "Echocardiogram",
            "frequency_months": 24,
            "recommendation": "Consider repeat echo to assess cardiac function",
            "priority": 1,
        },
        "stress_test": {
            "description": "Cardiac stress test",
            "frequency_months": 24,
            "recommendation": "Consider stress test if symptomatic",
            "priority": 1,
        },
    }

    # CKD care
    CKD_CARE = {
        "creatinine": {
            "description": "Renal function monitoring",
            "frequency_months": 3,  # More frequent for CKD
            "recommendation": "Check creatinine and eGFR",
            "priority": 3,
        },
        "urine_acr": {
            "description": "Proteinuria monitoring",
            "frequency_months": 6,
            "recommendation": "Check urine ACR for proteinuria progression",
            "priority": 2,
        },
        "phosphorus": {
            "description": "Phosphorus level",
            "frequency_months": 6,
            "recommendation": "Check phosphorus (CKD mineral bone disease)",
            "priority": 2,
        },
        "pth": {
            "description": "Parathyroid hormone",
            "frequency_months": 12,
            "recommendation": "Check PTH if CKD stage 3+",
            "priority": 1,
        },
    }

    # Medication-specific monitoring
    MEDICATION_MONITORING = {
        "statin": {
            "tests": ["liver_function"],
            "frequency_months": 12,
            "recommendation": "Check LFT annually for patients on statins",
            "priority": 1,
        },
        "metformin": {
            "tests": ["creatinine", "b12"],
            "frequency_months": 12,
            "recommendation": "Check renal function and B12 annually",
            "priority": 2,
        },
        "ace_inhibitor": {
            "tests": ["creatinine", "potassium"],
            "frequency_months": 6,
            "recommendation": "Check renal function and potassium",
            "priority": 2,
        },
        "arb": {
            "tests": ["creatinine", "potassium"],
            "frequency_months": 6,
            "recommendation": "Check renal function and potassium",
            "priority": 2,
        },
        "warfarin": {
            "tests": ["inr"],
            "frequency_months": 1,
            "recommendation": "Check INR monthly (or as indicated)",
            "priority": 3,
        },
        "lithium": {
            "tests": ["lithium_level", "thyroid", "creatinine"],
            "frequency_months": 3,
            "recommendation": "Check lithium level, thyroid, and renal function",
            "priority": 3,
        },
        "carbamazepine": {
            "tests": ["cbc", "liver_function", "sodium"],
            "frequency_months": 6,
            "recommendation": "Check CBC, LFT, and sodium",
            "priority": 2,
        },
        "amiodarone": {
            "tests": ["thyroid", "liver_function", "chest_xray"],
            "frequency_months": 6,
            "recommendation": "Check TFT, LFT, and chest X-ray",
            "priority": 2,
        },
    }

    # Preventive care by age/gender
    PREVENTIVE_CARE = {
        "annual_physical": {
            "description": "Annual health checkup",
            "frequency_months": 12,
            "min_age": 40,
            "recommendation": "Schedule annual wellness visit",
            "priority": 1,
        },
        "colonoscopy": {
            "description": "Colorectal cancer screening",
            "frequency_months": 120,  # 10 years
            "min_age": 45,
            "recommendation": "Refer for colonoscopy screening",
            "priority": 1,
        },
        "mammogram": {
            "description": "Breast cancer screening",
            "frequency_months": 24,
            "min_age": 40,
            "gender": "F",
            "recommendation": "Refer for mammography",
            "priority": 2,
        },
        "pap_smear": {
            "description": "Cervical cancer screening",
            "frequency_months": 36,
            "min_age": 21,
            "max_age": 65,
            "gender": "F",
            "recommendation": "Order Pap smear/HPV test",
            "priority": 2,
        },
        "flu_vaccine": {
            "description": "Influenza vaccination",
            "frequency_months": 12,
            "recommendation": "Administer annual flu vaccine",
            "priority": 2,
        },
        "pneumonia_vaccine": {
            "description": "Pneumococcal vaccination",
            "frequency_months": 60,  # 5 years for some, once for others
            "min_age": 65,
            "recommendation": "Administer pneumococcal vaccine if due",
            "priority": 1,
        },
        "bone_density": {
            "description": "Bone density scan",
            "frequency_months": 24,
            "min_age": 65,
            "gender": "F",
            "recommendation": "Order DEXA scan for osteoporosis screening",
            "priority": 1,
        },
        "aaa_screening": {
            "description": "Abdominal aortic aneurysm screening",
            "frequency_months": 0,  # Once
            "min_age": 65,
            "max_age": 75,
            "gender": "M",
            "smoking_history": True,
            "recommendation": "Order abdominal ultrasound for AAA screening",
            "priority": 1,
        },
    }

    def __init__(self, db_service=None):
        """Initialize care gap detector."""
        self.db = db_service

    def detect_care_gaps(
        self,
        patient_conditions: List[str],
        current_medications: List[str],
        last_tests: Dict[str, date],
        age: int,
        gender: str,
        smoking_history: bool = False,
        today: date = None
    ) -> List[CareGap]:
        """
        Detect all care gaps for a patient.

        Args:
            patient_conditions: List of patient diagnoses (e.g., ['diabetes', 'hypertension'])
            current_medications: List of current medications
            last_tests: Dict mapping test names to last performed date
            age: Patient age in years
            gender: 'M' or 'F'
            smoking_history: Whether patient has smoking history
            today: Current date (defaults to today)

        Returns:
            List of CareGap objects sorted by priority
        """
        if today is None:
            today = date.today()

        gaps = []

        # Normalize conditions to lowercase
        conditions = [c.lower() for c in patient_conditions]
        medications = [m.lower() for m in current_medications]

        # Check condition-specific care gaps
        if any(c in conditions for c in ['diabetes', 'dm', 'type 2 diabetes', 'type 1 diabetes']):
            gaps.extend(self._check_condition_care(
                self.DIABETES_CARE, last_tests, today, ['diabetes']
            ))

        if any(c in conditions for c in ['hypertension', 'htn', 'high blood pressure']):
            gaps.extend(self._check_condition_care(
                self.HYPERTENSION_CARE, last_tests, today, ['hypertension']
            ))

        if any(c in conditions for c in ['cad', 'coronary artery disease', 'ihd', 'mi', 'stemi', 'nstemi']):
            gaps.extend(self._check_condition_care(
                self.CAD_CARE, last_tests, today, ['CAD']
            ))

        if any(c in conditions for c in ['ckd', 'chronic kidney disease', 'renal failure']):
            gaps.extend(self._check_condition_care(
                self.CKD_CARE, last_tests, today, ['CKD']
            ))

        # Check medication monitoring
        gaps.extend(self._check_medication_monitoring(
            medications, last_tests, today
        ))

        # Check preventive care
        gaps.extend(self._check_preventive_care(
            age, gender, smoking_history, last_tests, today
        ))

        # Remove duplicates (same test from multiple conditions)
        gaps = self._deduplicate_gaps(gaps)

        # Sort by priority (highest first), then by days overdue
        gaps.sort(key=lambda g: (-g.priority, -g.days_overdue))

        return gaps

    def _check_condition_care(
        self,
        care_schedule: Dict,
        last_tests: Dict[str, date],
        today: date,
        applies_to: List[str]
    ) -> List[CareGap]:
        """Check care gaps for a specific condition."""
        gaps = []

        for test_key, care_info in care_schedule.items():
            gap = self._check_single_test(
                test_key=test_key,
                care_info=care_info,
                last_tests=last_tests,
                today=today,
                applies_to=applies_to
            )
            if gap:
                gaps.append(gap)

        return gaps

    def _check_single_test(
        self,
        test_key: str,
        care_info: Dict,
        last_tests: Dict[str, date],
        today: date,
        applies_to: List[str]
    ) -> Optional[CareGap]:
        """Check if a single test is due."""
        frequency_months = care_info["frequency_months"]
        last_performed = last_tests.get(test_key)

        if last_performed:
            due_date = last_performed + timedelta(days=frequency_months * 30)
        else:
            # Never performed - due now
            due_date = today - timedelta(days=1)

        days_overdue = (today - due_date).days

        if days_overdue > 0:
            severity = GapSeverity.OVERDUE
        elif days_overdue > -30:
            severity = GapSeverity.DUE_SOON
        else:
            return None  # Not due yet

        return CareGap(
            care_type=test_key,
            description=care_info["description"],
            last_performed=last_performed,
            due_date=due_date,
            days_overdue=days_overdue,
            severity=severity,
            recommendation=care_info["recommendation"],
            applies_to=applies_to,
            priority=care_info.get("priority", 1),
        )

    def _check_medication_monitoring(
        self,
        medications: List[str],
        last_tests: Dict[str, date],
        today: date
    ) -> List[CareGap]:
        """Check monitoring gaps for current medications."""
        gaps = []

        for med_class, monitoring in self.MEDICATION_MONITORING.items():
            # Check if any medication matches this class
            if self._patient_on_medication_class(medications, med_class):
                for test in monitoring["tests"]:
                    gap = self._check_single_test(
                        test_key=test,
                        care_info={
                            "description": f"{test.replace('_', ' ').title()} for {med_class}",
                            "frequency_months": monitoring["frequency_months"],
                            "recommendation": monitoring["recommendation"],
                            "priority": monitoring.get("priority", 2),
                        },
                        last_tests=last_tests,
                        today=today,
                        applies_to=[f"On {med_class}"]
                    )
                    if gap:
                        gaps.append(gap)

        return gaps

    def _patient_on_medication_class(
        self,
        medications: List[str],
        med_class: str
    ) -> bool:
        """Check if patient is on a medication class."""
        medication_classes = {
            "statin": ["atorvastatin", "rosuvastatin", "simvastatin", "pravastatin", "pitavastatin"],
            "metformin": ["metformin", "glucophage"],
            "ace_inhibitor": ["lisinopril", "enalapril", "ramipril", "captopril", "perindopril"],
            "arb": ["losartan", "valsartan", "telmisartan", "olmesartan", "irbesartan"],
            "warfarin": ["warfarin", "coumadin"],
            "lithium": ["lithium"],
            "carbamazepine": ["carbamazepine", "tegretol"],
            "amiodarone": ["amiodarone", "cordarone"],
        }

        drugs_in_class = medication_classes.get(med_class, [])
        for med in medications:
            med_lower = med.lower()
            if any(drug in med_lower for drug in drugs_in_class):
                return True
        return False

    def _check_preventive_care(
        self,
        age: int,
        gender: str,
        smoking_history: bool,
        last_tests: Dict[str, date],
        today: date
    ) -> List[CareGap]:
        """Check preventive care gaps based on age and gender."""
        gaps = []

        for care_key, care_info in self.PREVENTIVE_CARE.items():
            # Check age requirements
            min_age = care_info.get("min_age", 0)
            max_age = care_info.get("max_age", 150)
            if not (min_age <= age <= max_age):
                continue

            # Check gender requirements
            required_gender = care_info.get("gender")
            if required_gender and gender.upper() != required_gender:
                continue

            # Check smoking requirement
            if care_info.get("smoking_history") and not smoking_history:
                continue

            # Check if test is due
            gap = self._check_single_test(
                test_key=care_key,
                care_info=care_info,
                last_tests=last_tests,
                today=today,
                applies_to=["Preventive care"]
            )
            if gap:
                gaps.append(gap)

        return gaps

    def _deduplicate_gaps(self, gaps: List[CareGap]) -> List[CareGap]:
        """Remove duplicate gaps, keeping the one with highest priority."""
        seen = {}
        for gap in gaps:
            key = gap.care_type
            if key not in seen or gap.priority > seen[key].priority:
                # Merge applies_to lists
                if key in seen:
                    gap.applies_to = list(set(gap.applies_to + seen[key].applies_to))
                seen[key] = gap
        return list(seen.values())

    def get_actionable_gaps(self, gaps: List[CareGap]) -> List[CareGap]:
        """Get gaps that need immediate action (overdue or high priority)."""
        return [
            g for g in gaps
            if g.severity == GapSeverity.OVERDUE or g.priority >= 3
        ]

    def get_gaps_by_severity(
        self,
        gaps: List[CareGap]
    ) -> Dict[GapSeverity, List[CareGap]]:
        """Group gaps by severity."""
        result = {
            GapSeverity.OVERDUE: [],
            GapSeverity.DUE_SOON: [],
            GapSeverity.RECOMMENDED: [],
        }
        for gap in gaps:
            result[gap.severity].append(gap)
        return result

    def format_gaps_for_display(self, gaps: List[CareGap]) -> List[str]:
        """Format gaps as human-readable strings."""
        formatted = []
        for gap in gaps:
            if gap.last_performed:
                last_str = gap.last_performed.strftime("%b %Y")
                if gap.days_overdue > 0:
                    formatted.append(
                        f"⚠️ {gap.description} - overdue by {gap.days_overdue} days (last: {last_str})"
                    )
                else:
                    formatted.append(
                        f"📅 {gap.description} - due soon (last: {last_str})"
                    )
            else:
                formatted.append(
                    f"❗ {gap.description} - never performed"
                )
        return formatted
