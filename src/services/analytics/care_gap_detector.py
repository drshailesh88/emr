"""Care gap detector for preventive care and follow-up monitoring."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Tuple
from enum import Enum
import json
import re


class CareGapPriority(Enum):
    """Priority levels for care gaps."""
    URGENT = "urgent"  # Overdue >30 days or critical
    SOON = "soon"  # Due within 7-30 days
    ROUTINE = "routine"  # Due within 30-90 days


@dataclass
class CareGap:
    """Represents a detected care gap."""
    patient_id: int
    category: str  # preventive, monitoring, follow_up
    description: str
    recommendation: str
    priority: CareGapPriority
    days_overdue: Optional[int] = None
    last_done_date: Optional[date] = None
    details: Optional[str] = None
    action_type: str = "order"  # order, reminder, schedule


class CareGapDetector:
    """Detects missing preventive care, overdue follow-ups, and monitoring gaps."""

    def __init__(self, db_service):
        """Initialize care gap detector.

        Args:
            db_service: DatabaseService instance for querying patient data
        """
        self.db = db_service

    def detect_care_gaps(self, patient_id: int) -> List[CareGap]:
        """Detect all care gaps for a patient.

        Args:
            patient_id: Patient ID to check

        Returns:
            List of CareGap objects sorted by priority
        """
        gaps = []

        # Get patient data
        patient = self.db.get_patient(patient_id)
        if not patient:
            return gaps

        # Get visits, investigations, procedures
        visits = self.db.get_patient_visits(patient_id)
        investigations = self.db.get_patient_investigations(patient_id)
        procedures = self.db.get_patient_procedures(patient_id)

        # Extract diagnoses and medications from visits
        diagnoses = self._extract_diagnoses(visits)
        medications = self._extract_medications(visits)

        # Check diabetes-related gaps
        if self._has_condition(diagnoses, ["diabetes", "dm", "t2dm", "t1dm", "diabetic"]):
            gaps.extend(self._check_diabetes_gaps(patient_id, investigations, procedures))

        # Check hypertension gaps
        if self._has_condition(diagnoses, ["hypertension", "htn", "high bp", "high blood pressure"]):
            gaps.extend(self._check_hypertension_gaps(patient_id, investigations))

        # Check medication-specific monitoring
        gaps.extend(self._check_medication_monitoring(medications, investigations))

        # Check age-based preventive care
        gaps.extend(self._check_preventive_care(patient, procedures))

        # Check overdue follow-ups
        gaps.extend(self._check_overdue_followups(visits))

        # Sort by priority (urgent first)
        priority_order = {
            CareGapPriority.URGENT: 0,
            CareGapPriority.SOON: 1,
            CareGapPriority.ROUTINE: 2,
        }
        gaps.sort(key=lambda g: priority_order[g.priority])

        return gaps

    def _extract_diagnoses(self, visits) -> List[str]:
        """Extract all diagnoses from visits.

        Args:
            visits: List of Visit objects

        Returns:
            List of diagnosis strings (lowercased)
        """
        diagnoses = []
        for visit in visits:
            if visit.diagnosis:
                diagnoses.append(visit.diagnosis.lower())
            # Also check chief complaint for chronic conditions
            if visit.chief_complaint:
                diagnoses.append(visit.chief_complaint.lower())
        return diagnoses

    def _extract_medications(self, visits) -> List[str]:
        """Extract all medications from visits.

        Args:
            visits: List of Visit objects

        Returns:
            List of medication names (lowercased)
        """
        medications = []
        for visit in visits:
            if visit.prescription_json:
                try:
                    rx = json.loads(visit.prescription_json)
                    for med in rx.get("medications", []):
                        drug_name = med.get("drug_name", "").lower()
                        if drug_name:
                            medications.append(drug_name)
                except (json.JSONDecodeError, KeyError):
                    pass
        return medications

    def _has_condition(self, diagnoses: List[str], keywords: List[str]) -> bool:
        """Check if patient has a condition based on keywords.

        Args:
            diagnoses: List of diagnosis strings
            keywords: List of keywords to search for

        Returns:
            True if any keyword found in diagnoses
        """
        for diagnosis in diagnoses:
            for keyword in keywords:
                if keyword in diagnosis:
                    return True
        return False

    def _has_medication(self, medications: List[str], keywords: List[str]) -> bool:
        """Check if patient is on a medication based on keywords.

        Args:
            medications: List of medication names
            keywords: List of keywords to search for

        Returns:
            True if any keyword found in medications
        """
        for med in medications:
            for keyword in keywords:
                if keyword in med:
                    return True
        return False

    def _get_latest_test(self, investigations, test_names: List[str]) -> Optional[Tuple[date, str]]:
        """Get the latest test date for given test names.

        Args:
            investigations: List of Investigation objects
            test_names: List of test name keywords to search for

        Returns:
            Tuple of (test_date, test_name) if found, None otherwise
        """
        latest_date = None
        latest_name = None

        for inv in investigations:
            test_name_lower = inv.test_name.lower()
            for keyword in test_names:
                if keyword in test_name_lower and inv.test_date:
                    if latest_date is None or inv.test_date > latest_date:
                        latest_date = inv.test_date
                        latest_name = inv.test_name

        return (latest_date, latest_name) if latest_date else None

    def _check_diabetes_gaps(self, patient_id: int, investigations, procedures) -> List[CareGap]:
        """Check diabetes-related care gaps.

        Args:
            patient_id: Patient ID
            investigations: List of Investigation objects
            procedures: List of Procedure objects

        Returns:
            List of CareGap objects
        """
        gaps = []
        today = date.today()

        # HbA1c - should be done every 3 months
        hba1c_result = self._get_latest_test(investigations, ["hba1c", "glycated", "a1c"])
        if hba1c_result:
            last_date, test_name = hba1c_result
            days_since = (today - last_date).days
            if days_since > 90:
                priority = CareGapPriority.URGENT if days_since > 150 else CareGapPriority.SOON
                gaps.append(CareGap(
                    patient_id=patient_id,
                    category="monitoring",
                    description="HbA1c overdue",
                    recommendation=f"Order HbA1c test (last done {days_since} days ago)",
                    priority=priority,
                    days_overdue=days_since - 90,
                    last_done_date=last_date,
                    details=f"Last test: {test_name} on {last_date}",
                    action_type="order",
                ))
        else:
            gaps.append(CareGap(
                patient_id=patient_id,
                category="monitoring",
                description="HbA1c never done",
                recommendation="Order baseline HbA1c test for diabetes monitoring",
                priority=CareGapPriority.URGENT,
                details="No HbA1c test on record",
                action_type="order",
            ))

        # Eye exam - should be done yearly
        eye_exam_found = False
        for proc in procedures:
            proc_name_lower = proc.procedure_name.lower()
            if any(keyword in proc_name_lower for keyword in ["eye exam", "fundoscopy", "retinal", "ophthalmology"]):
                if proc.procedure_date:
                    days_since = (today - proc.procedure_date).days
                    if days_since > 365:
                        priority = CareGapPriority.URGENT if days_since > 450 else CareGapPriority.SOON
                        gaps.append(CareGap(
                            patient_id=patient_id,
                            category="preventive",
                            description="Diabetic eye exam overdue",
                            recommendation=f"Schedule ophthalmology consult (last done {days_since} days ago)",
                            priority=priority,
                            days_overdue=days_since - 365,
                            last_done_date=proc.procedure_date,
                            details=f"Last exam: {proc.procedure_name} on {proc.procedure_date}",
                            action_type="reminder",
                        ))
                    eye_exam_found = True
                    break

        if not eye_exam_found:
            gaps.append(CareGap(
                patient_id=patient_id,
                category="preventive",
                description="Diabetic eye exam not documented",
                recommendation="Schedule annual dilated eye exam for diabetic retinopathy screening",
                priority=CareGapPriority.URGENT,
                details="No eye exam on record",
                action_type="reminder",
            ))

        # Foot exam - should be documented in visits
        foot_exam_found = False
        visits = self.db.get_patient_visits(patient_id)
        for visit in visits[:5]:  # Check last 5 visits
            if visit.clinical_notes:
                notes_lower = visit.clinical_notes.lower()
                if any(keyword in notes_lower for keyword in ["foot exam", "feet exam", "pedal", "peripheral pulses"]):
                    foot_exam_found = True
                    break

        if not foot_exam_found:
            gaps.append(CareGap(
                patient_id=patient_id,
                category="preventive",
                description="Diabetic foot exam not documented",
                recommendation="Perform and document diabetic foot exam (check pulses, sensation, ulcers)",
                priority=CareGapPriority.ROUTINE,
                details="No foot exam in recent visits",
                action_type="reminder",
            ))

        return gaps

    def _check_hypertension_gaps(self, patient_id: int, investigations) -> List[CareGap]:
        """Check hypertension-related care gaps.

        Args:
            patient_id: Patient ID
            investigations: List of Investigation objects

        Returns:
            List of CareGap objects
        """
        gaps = []
        today = date.today()

        # Check if BP was recorded recently (via vitals, not investigations)
        # We'll check this in visits instead
        visits = self.db.get_patient_visits(patient_id)

        # Try to get vitals from database
        bp_recorded = False
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT recorded_at FROM vitals
                    WHERE patient_id = ? AND bp_systolic IS NOT NULL
                    ORDER BY recorded_at DESC LIMIT 1
                """, (patient_id,))
                result = cursor.fetchone()
                if result:
                    last_bp_date = datetime.fromisoformat(result[0]).date()
                    days_since = (today - last_bp_date).days
                    if days_since > 30:
                        priority = CareGapPriority.URGENT if days_since > 60 else CareGapPriority.SOON
                        gaps.append(CareGap(
                            patient_id=patient_id,
                            category="monitoring",
                            description="Blood pressure check overdue",
                            recommendation=f"Record blood pressure (last recorded {days_since} days ago)",
                            priority=priority,
                            days_overdue=days_since - 30,
                            last_done_date=last_bp_date,
                            details=f"Last BP: {last_bp_date}",
                            action_type="reminder",
                        ))
                    bp_recorded = True
        except Exception:
            pass

        if not bp_recorded:
            gaps.append(CareGap(
                patient_id=patient_id,
                category="monitoring",
                description="Blood pressure not recorded",
                recommendation="Record blood pressure for hypertension monitoring",
                priority=CareGapPriority.URGENT,
                details="No BP readings on record",
                action_type="reminder",
            ))

        return gaps

    def _check_medication_monitoring(self, medications: List[str], investigations) -> List[CareGap]:
        """Check medication-specific monitoring gaps.

        Args:
            medications: List of medication names
            investigations: List of Investigation objects

        Returns:
            List of CareGap objects
        """
        gaps = []
        today = date.today()
        patient_id = investigations[0].patient_id if investigations else None

        # Warfarin - INR should be checked monthly
        if self._has_medication(medications, ["warfarin", "coumadin"]):
            inr_result = self._get_latest_test(investigations, ["inr", "pt/inr"])
            if inr_result:
                last_date, test_name = inr_result
                days_since = (today - last_date).days
                if days_since > 30:
                    priority = CareGapPriority.URGENT if days_since > 45 else CareGapPriority.SOON
                    gaps.append(CareGap(
                        patient_id=patient_id,
                        category="monitoring",
                        description="INR check overdue (on Warfarin)",
                        recommendation=f"Order INR test (last done {days_since} days ago)",
                        priority=priority,
                        days_overdue=days_since - 30,
                        last_done_date=last_date,
                        details=f"Patient on warfarin. Last INR: {last_date}",
                        action_type="order",
                    ))
            else:
                gaps.append(CareGap(
                    patient_id=patient_id,
                    category="monitoring",
                    description="INR not checked (on Warfarin)",
                    recommendation="Order baseline INR for warfarin monitoring",
                    priority=CareGapPriority.URGENT,
                    details="Patient on warfarin, no INR on record",
                    action_type="order",
                ))

        # Metformin - Creatinine should be checked every 6 months
        if self._has_medication(medications, ["metformin"]):
            creat_result = self._get_latest_test(investigations, ["creatinine", "serum creat"])
            if creat_result:
                last_date, test_name = creat_result
                days_since = (today - last_date).days
                if days_since > 180:
                    priority = CareGapPriority.URGENT if days_since > 240 else CareGapPriority.ROUTINE
                    gaps.append(CareGap(
                        patient_id=patient_id,
                        category="monitoring",
                        description="Creatinine check overdue (on Metformin)",
                        recommendation=f"Order creatinine test (last done {days_since} days ago)",
                        priority=priority,
                        days_overdue=days_since - 180,
                        last_done_date=last_date,
                        details=f"Patient on metformin. Last creatinine: {last_date}",
                        action_type="order",
                    ))
            else:
                gaps.append(CareGap(
                    patient_id=patient_id,
                    category="monitoring",
                    description="Creatinine not checked (on Metformin)",
                    recommendation="Order baseline creatinine for metformin safety",
                    priority=CareGapPriority.SOON,
                    details="Patient on metformin, no creatinine on record",
                    action_type="order",
                ))

        # Statins - Lipid profile should be checked yearly
        if self._has_medication(medications, ["statin", "atorvastatin", "rosuvastatin", "simvastatin"]):
            lipid_result = self._get_latest_test(investigations, ["lipid", "cholesterol", "ldl", "hdl"])
            if lipid_result:
                last_date, test_name = lipid_result
                days_since = (today - last_date).days
                if days_since > 365:
                    priority = CareGapPriority.SOON if days_since > 450 else CareGapPriority.ROUTINE
                    gaps.append(CareGap(
                        patient_id=patient_id,
                        category="monitoring",
                        description="Lipid profile overdue (on Statin)",
                        recommendation=f"Order lipid profile (last done {days_since} days ago)",
                        priority=priority,
                        days_overdue=days_since - 365,
                        last_done_date=last_date,
                        details=f"Patient on statin. Last lipid profile: {last_date}",
                        action_type="order",
                    ))
            else:
                gaps.append(CareGap(
                    patient_id=patient_id,
                    category="monitoring",
                    description="Lipid profile not checked (on Statin)",
                    recommendation="Order baseline lipid profile for statin therapy",
                    priority=CareGapPriority.ROUTINE,
                    details="Patient on statin, no lipid profile on record",
                    action_type="order",
                ))

        return gaps

    def _check_preventive_care(self, patient, procedures) -> List[CareGap]:
        """Check age-based preventive care gaps.

        Args:
            patient: Patient object
            procedures: List of Procedure objects

        Returns:
            List of CareGap objects
        """
        gaps = []
        today = date.today()

        if not patient.age:
            return gaps

        # Colonoscopy for age >50
        if patient.age > 50:
            colonoscopy_found = False
            for proc in procedures:
                if "colonoscopy" in proc.procedure_name.lower():
                    colonoscopy_found = True
                    # Check if >10 years old
                    if proc.procedure_date:
                        days_since = (today - proc.procedure_date).days
                        if days_since > 3650:  # 10 years
                            gaps.append(CareGap(
                                patient_id=patient.id,
                                category="preventive",
                                description="Colonoscopy screening due",
                                recommendation="Consider repeat colonoscopy (last done >10 years ago)",
                                priority=CareGapPriority.ROUTINE,
                                last_done_date=proc.procedure_date,
                                details=f"Last colonoscopy: {proc.procedure_date}",
                                action_type="reminder",
                            ))
                    break

            if not colonoscopy_found:
                gaps.append(CareGap(
                    patient_id=patient.id,
                    category="preventive",
                    description="Colonoscopy screening recommended",
                    recommendation=f"Consider colonoscopy for colorectal cancer screening (age {patient.age})",
                    priority=CareGapPriority.ROUTINE,
                    details="Age-appropriate screening",
                    action_type="reminder",
                ))

        # Mammogram for women >40
        if patient.gender in ["F", "f"] and patient.age > 40:
            mammogram_found = False
            for proc in procedures:
                if "mammogram" in proc.procedure_name.lower():
                    mammogram_found = True
                    # Check if >2 years old
                    if proc.procedure_date:
                        days_since = (today - proc.procedure_date).days
                        if days_since > 730:  # 2 years
                            priority = CareGapPriority.SOON if days_since > 900 else CareGapPriority.ROUTINE
                            gaps.append(CareGap(
                                patient_id=patient.id,
                                category="preventive",
                                description="Mammogram screening due",
                                recommendation=f"Schedule mammogram (last done {days_since // 365} years ago)",
                                priority=priority,
                                days_overdue=days_since - 730,
                                last_done_date=proc.procedure_date,
                                details=f"Last mammogram: {proc.procedure_date}",
                                action_type="reminder",
                            ))
                    break

            if not mammogram_found:
                gaps.append(CareGap(
                    patient_id=patient.id,
                    category="preventive",
                    description="Mammogram screening recommended",
                    recommendation=f"Schedule baseline/screening mammogram (age {patient.age})",
                    priority=CareGapPriority.ROUTINE,
                    details="Age-appropriate screening",
                    action_type="reminder",
                ))

        return gaps

    def _check_overdue_followups(self, visits) -> List[CareGap]:
        """Check for overdue follow-up appointments.

        Args:
            visits: List of Visit objects

        Returns:
            List of CareGap objects
        """
        gaps = []
        today = date.today()

        if not visits:
            return gaps

        # Check the most recent visit for follow-up
        latest_visit = visits[0]
        if latest_visit.prescription_json:
            try:
                rx = json.loads(latest_visit.prescription_json)
                follow_up = rx.get("follow_up", "")

                if follow_up:
                    # Try to parse follow-up timing
                    follow_up_lower = follow_up.lower()
                    follow_up_date = None

                    # Extract number of days/weeks
                    if "week" in follow_up_lower:
                        match = re.search(r'(\d+)\s*week', follow_up_lower)
                        if match:
                            weeks = int(match.group(1))
                            follow_up_date = latest_visit.visit_date + timedelta(weeks=weeks)
                    elif "day" in follow_up_lower:
                        match = re.search(r'(\d+)\s*day', follow_up_lower)
                        if match:
                            days = int(match.group(1))
                            follow_up_date = latest_visit.visit_date + timedelta(days=days)
                    elif "month" in follow_up_lower:
                        match = re.search(r'(\d+)\s*month', follow_up_lower)
                        if match:
                            months = int(match.group(1))
                            follow_up_date = latest_visit.visit_date + timedelta(days=months * 30)

                    # Check if overdue
                    if follow_up_date and today > follow_up_date:
                        days_overdue = (today - follow_up_date).days
                        if days_overdue > 7:
                            priority = CareGapPriority.URGENT if days_overdue > 30 else CareGapPriority.SOON
                            gaps.append(CareGap(
                                patient_id=latest_visit.patient_id,
                                category="follow_up",
                                description="Follow-up appointment overdue",
                                recommendation=f"Schedule follow-up visit ({days_overdue} days overdue)",
                                priority=priority,
                                days_overdue=days_overdue,
                                last_done_date=latest_visit.visit_date,
                                details=f"Last visit: {latest_visit.visit_date}. Advised: {follow_up}",
                                action_type="reminder",
                            ))
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        return gaps

    def generate_care_gap_report(self, all_patients: bool = False) -> Dict[str, List[CareGap]]:
        """Generate care gap report for all patients or selected patients.

        Args:
            all_patients: If True, check all patients in database

        Returns:
            Dictionary mapping patient UHID to list of care gaps
        """
        report = {}

        if all_patients:
            patients = self.db.search_patients("")  # Get all patients
        else:
            return report

        for patient in patients:
            gaps = self.detect_care_gaps(patient.id)
            if gaps:
                uhid = patient.uhid or f"Patient {patient.id}"
                report[uhid] = gaps

        return report
