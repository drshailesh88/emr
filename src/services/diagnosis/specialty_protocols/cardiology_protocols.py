"""
Cardiology Clinical Protocols

Evidence-based protocols for cardiovascular conditions in Indian practice.
Based on ACC/AHA, ESC, CSI (Cardiological Society of India) guidelines.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from ..protocol_engine import (
    TreatmentProtocol,
    Medication,
    DrugRoute,
    ComplianceReport,
    ComplianceIssue,
)


@dataclass
class RedFlag:
    """Red flag warning requiring immediate attention."""
    symptom: str
    urgency: str  # EMERGENCY, URGENT, MONITOR
    action: str


class CardiologyProtocols:
    """
    Cardiology-specific treatment protocols.

    Implements evidence-based management for:
    - Acute Coronary Syndrome (STEMI/NSTEMI)
    - Heart Failure (HFrEF/HFpEF)
    - Atrial Fibrillation
    - Hypertension (Indian-specific)
    """

    def __init__(self):
        """Initialize cardiology protocols."""
        self._load_protocols()

    def _load_protocols(self) -> None:
        """Load cardiology-specific protocols."""
        self.protocols = {
            "stemi": self._stemi_protocol(),
            "nstemi": self._nstemi_protocol(),
            "unstable_angina": self._unstable_angina_protocol(),
            "heart_failure_hfref": self._heart_failure_hfref_protocol(),
            "heart_failure_hfpef": self._heart_failure_hfpef_protocol(),
            "atrial_fibrillation": self._atrial_fibrillation_protocol(),
            "hypertension_stage1": self._hypertension_stage1_protocol(),
            "hypertension_stage2": self._hypertension_stage2_protocol(),
        }

    def _stemi_protocol(self) -> TreatmentProtocol:
        """STEMI (ST-Elevation Myocardial Infarction) protocol."""
        return TreatmentProtocol(
            diagnosis="STEMI (ST-Elevation Myocardial Infarction)",
            icd10_code="I21.3",
            first_line_drugs=[
                # MONA protocol
                Medication(
                    drug_name="Aspirin",
                    generic_name="Aspirin",
                    strength="325mg",
                    form="tablet",
                    dose="4 tablets (chew)",
                    frequency="STAT",
                    instructions="chew immediately",
                    indication="Antiplatelet - STAT loading dose",
                ),
                Medication(
                    drug_name="Clopidogrel",
                    generic_name="Clopidogrel",
                    strength="75mg",
                    form="tablet",
                    dose="8 tablets (600mg)",
                    frequency="STAT loading, then 75mg OD",
                    duration="12 months minimum",
                    indication="Dual antiplatelet therapy",
                ),
                Medication(
                    drug_name="Atorvastatin",
                    generic_name="Atorvastatin",
                    strength="80mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="lifelong",
                    instructions="high-intensity statin",
                    indication="Lipid lowering, plaque stabilization",
                ),
                Medication(
                    drug_name="Metoprolol",
                    generic_name="Metoprolol",
                    strength="25mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="lifelong",
                    instructions="if no bradycardia/hypotension",
                    indication="Beta-blocker for mortality reduction",
                ),
                Medication(
                    drug_name="Ramipril",
                    generic_name="Ramipril",
                    strength="2.5mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="lifelong",
                    instructions="start within 24h, uptitrate",
                    indication="ACE inhibitor for remodeling prevention",
                ),
                Medication(
                    drug_name="Glyceryl Trinitrate",
                    generic_name="GTN",
                    strength="0.5mg",
                    form="sublingual tablet",
                    dose="1",
                    frequency="SOS",
                    instructions="for chest pain, max 3 doses 5 min apart",
                    indication="Nitrate for symptom relief",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Ticagrelor",
                    generic_name="Ticagrelor",
                    strength="90mg",
                    form="tablet",
                    dose="2 tablets loading (180mg), then 1 BD",
                    frequency="BD",
                    duration="12 months",
                    indication="Alternative to clopidogrel (superior efficacy)",
                ),
                Medication(
                    drug_name="Prasugrel",
                    generic_name="Prasugrel",
                    strength="10mg",
                    form="tablet",
                    dose="6 tablets loading (60mg), then 1 OD",
                    frequency="OD",
                    duration="12 months",
                    indication="Alternative P2Y12 inhibitor",
                ),
            ],
            investigations=[
                "ECG (immediate, repeat q15min)",
                "Troponin I/T (0h, 3h, 6h)",
                "CBC, PT/INR, aPTT",
                "Lipid profile (within 24h)",
                "HbA1c, FBS",
                "Serum creatinine, electrolytes",
                "2D Echo (within 24h)",
                "Coronary angiography (immediate - door-to-balloon <90 min)",
                "Chest X-ray",
            ],
            monitoring=[
                "Continuous ECG monitoring",
                "Vital signs q15min until stable",
                "Troponin serial monitoring",
                "Door-to-balloon time (target <90 min)",
                "Post-PCI: Bleeding, contrast nephropathy",
                "Echo at discharge for EF",
            ],
            lifestyle_advice=[
                "ABSOLUTE smoking cessation",
                "Cardiac rehabilitation program",
                "Mediterranean/DASH diet",
                "Salt restriction <2g/day",
                "Gradual return to activity (supervised)",
                "Stress management, psychological counseling",
            ],
            follow_up_interval="1 week post-discharge, then monthly x 3",
            referral_criteria=[
                "ALL STEMI patients need immediate cardiology referral",
                "Transfer to cath lab immediately",
                "If PCI not available within 90 min: consider fibrinolysis",
            ],
            contraindications={
                "aspirin": ["Active bleeding", "Severe bleeding disorder"],
                "beta_blockers": ["HR <60", "SBP <100", "2nd/3rd degree heart block", "Severe asthma"],
                "ace_inhibitors": ["Pregnancy", "Bilateral RAS", "Cr >3.0"],
            },
            drug_interactions=[
                "Clopidogrel + PPI (omeprazole) - reduced efficacy",
                "Aspirin + NSAIDs - increased bleeding risk",
            ],
        )

    def _nstemi_protocol(self) -> TreatmentProtocol:
        """NSTEMI (Non-ST-Elevation MI) protocol."""
        return TreatmentProtocol(
            diagnosis="NSTEMI (Non-ST-Elevation Myocardial Infarction)",
            icd10_code="I21.4",
            first_line_drugs=[
                Medication(
                    drug_name="Aspirin",
                    generic_name="Aspirin",
                    strength="325mg",
                    form="tablet",
                    dose="4 tablets (chew)",
                    frequency="STAT, then 75-150mg OD",
                    duration="lifelong",
                    indication="Antiplatelet",
                ),
                Medication(
                    drug_name="Ticagrelor",
                    generic_name="Ticagrelor",
                    strength="90mg",
                    form="tablet",
                    dose="2 tablets loading, then 1 BD",
                    frequency="BD",
                    duration="12 months",
                    indication="Preferred P2Y12 inhibitor for NSTEMI",
                ),
                Medication(
                    drug_name="Enoxaparin",
                    generic_name="Enoxaparin",
                    strength="60mg",
                    form="injection",
                    dose="1mg/kg",
                    frequency="BD",
                    route=DrugRoute.SC,
                    duration="Until revascularization",
                    indication="Anticoagulation",
                ),
                Medication(
                    drug_name="Atorvastatin",
                    generic_name="Atorvastatin",
                    strength="80mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="lifelong",
                    indication="High-intensity statin",
                ),
                Medication(
                    drug_name="Metoprolol",
                    generic_name="Metoprolol",
                    strength="25mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="lifelong",
                    indication="Beta-blocker",
                ),
            ],
            investigations=[
                "ECG (serial)",
                "Troponin I/T (0h, 3h - for diagnosis)",
                "GRACE score calculation",
                "CBC, renal function, electrolytes",
                "Lipid profile",
                "2D Echo",
                "Coronary angiography (within 24-72h based on GRACE score)",
            ],
            monitoring=[
                "Continuous ECG monitoring",
                "Troponin trend",
                "GRACE score (risk stratification)",
                "Bleeding complications",
            ],
            lifestyle_advice=[
                "Smoking cessation",
                "Cardiac rehabilitation",
                "Diet modification",
                "Stress reduction",
            ],
            follow_up_interval="1 week, then monthly",
            referral_criteria=[
                "All NSTEMI need cardiology referral",
                "High GRACE score (>140): urgent angiography within 24h",
                "Intermediate risk: angiography within 72h",
            ],
        )

    def _unstable_angina_protocol(self) -> TreatmentProtocol:
        """Unstable Angina protocol."""
        return TreatmentProtocol(
            diagnosis="Unstable Angina",
            icd10_code="I20.0",
            first_line_drugs=[
                Medication(
                    drug_name="Aspirin",
                    generic_name="Aspirin",
                    strength="150mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="lifelong",
                    indication="Antiplatelet",
                ),
                Medication(
                    drug_name="Clopidogrel",
                    generic_name="Clopidogrel",
                    strength="75mg",
                    form="tablet",
                    dose="4 tablets loading, then 1 OD",
                    frequency="OD",
                    duration="12 months",
                    indication="Dual antiplatelet",
                ),
                Medication(
                    drug_name="Isosorbide Mononitrate",
                    generic_name="Isosorbide Mononitrate",
                    strength="40mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    instructions="8am and 2pm (nitrate-free interval)",
                    indication="Long-acting nitrate",
                ),
                Medication(
                    drug_name="Atorvastatin",
                    generic_name="Atorvastatin",
                    strength="40mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    duration="lifelong",
                    indication="Statin",
                ),
            ],
            investigations=[
                "ECG (may be normal)",
                "Troponin (negative in UA)",
                "Stress test or CT coronary angiography",
                "2D Echo",
                "Lipid profile",
            ],
            monitoring=["Symptom frequency", "Exercise tolerance"],
            lifestyle_advice=[
                "Smoking cessation",
                "Regular exercise (after stabilization)",
                "Diet modification",
            ],
            follow_up_interval="2 weeks",
            referral_criteria=[
                "Recurrent symptoms despite medical therapy",
                "Positive stress test",
            ],
        )

    def _heart_failure_hfref_protocol(self) -> TreatmentProtocol:
        """Heart Failure with Reduced Ejection Fraction (HFrEF) protocol."""
        return TreatmentProtocol(
            diagnosis="Heart Failure with Reduced EF (HFrEF)",
            icd10_code="I50.1",
            first_line_drugs=[
                # Quadruple therapy (GDMT)
                Medication(
                    drug_name="Sacubitril/Valsartan (ARNI)",
                    generic_name="Sacubitril/Valsartan",
                    strength="50mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    instructions="uptitrate to 200mg BD",
                    indication="ARNI - superior to ACE-I alone",
                ),
                Medication(
                    drug_name="Carvedilol",
                    generic_name="Carvedilol",
                    strength="3.125mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    instructions="uptitrate to 25mg BD",
                    indication="Beta-blocker with mortality benefit",
                ),
                Medication(
                    drug_name="Spironolactone",
                    generic_name="Spironolactone",
                    strength="25mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    instructions="monitor K+",
                    indication="MRA - reduces hospitalization",
                ),
                Medication(
                    drug_name="Dapagliflozin (SGLT2i)",
                    generic_name="Dapagliflozin",
                    strength="10mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    indication="SGLT2i - even in non-diabetics",
                ),
                Medication(
                    drug_name="Furosemide",
                    generic_name="Furosemide",
                    strength="40mg",
                    form="tablet",
                    dose="1-2",
                    frequency="OD-BD",
                    instructions="for symptom relief (congestion)",
                    indication="Loop diuretic",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Digoxin",
                    generic_name="Digoxin",
                    strength="0.25mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    indication="If persistent symptoms or AFib",
                ),
                Medication(
                    drug_name="Ivabradine",
                    generic_name="Ivabradine",
                    strength="5mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    indication="If HR >70 despite beta-blocker",
                ),
            ],
            investigations=[
                "2D Echo (EF, wall motion, valves)",
                "BNP or NT-proBNP (diagnosis & monitoring)",
                "ECG",
                "Chest X-ray",
                "CBC, renal function, electrolytes (K+)",
                "LFT, TSH",
                "Lipid profile",
            ],
            monitoring=[
                "BNP/NT-proBNP levels",
                "Daily weight (report gain >2kg in 3 days)",
                "BP, HR at every visit",
                "Renal function, K+ (especially with ARNI + MRA)",
                "Symptoms (NYHA class)",
                "Echo yearly",
            ],
            lifestyle_advice=[
                "Fluid restriction 1.5L/day if severe",
                "Salt restriction <2g/day",
                "Daily weight monitoring",
                "Avoid NSAIDs",
                "Vaccinations (flu, pneumococcal)",
                "Cardiac rehabilitation",
            ],
            follow_up_interval="2 weeks initially, then monthly",
            referral_criteria=[
                "EF <35% despite GDMT - consider ICD",
                "NYHA III-IV despite therapy - advanced HF clinic",
                "Cardiogenic shock",
                "Refractory symptoms",
            ],
            contraindications={
                "arni": ["Angioedema history with ACE-I", "Pregnancy"],
                "beta_blockers": ["Decompensated HF", "HR <50", "Severe asthma"],
                "mra": ["K+ >5.0", "Cr >2.5"],
            },
        )

    def _heart_failure_hfpef_protocol(self) -> TreatmentProtocol:
        """Heart Failure with Preserved Ejection Fraction (HFpEF) protocol."""
        return TreatmentProtocol(
            diagnosis="Heart Failure with Preserved EF (HFpEF)",
            icd10_code="I50.9",
            first_line_drugs=[
                Medication(
                    drug_name="Furosemide",
                    generic_name="Furosemide",
                    strength="40mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    indication="Diuretic for congestion",
                ),
                Medication(
                    drug_name="Telmisartan",
                    generic_name="Telmisartan",
                    strength="40mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    indication="ARB for BP control",
                ),
                Medication(
                    drug_name="Dapagliflozin",
                    generic_name="Dapagliflozin",
                    strength="10mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    indication="SGLT2i - proven benefit in HFpEF",
                ),
            ],
            investigations=[
                "2D Echo (EF >50%, diastolic dysfunction)",
                "BNP/NT-proBNP",
                "ECG",
                "Stress echo or cardiac MRI",
            ],
            monitoring=["Symptoms", "BNP", "Echo"],
            lifestyle_advice=[
                "Salt restriction",
                "Weight loss if obese",
                "BP control",
                "Treat comorbidities (DM, AF)",
            ],
            follow_up_interval="Monthly",
            referral_criteria=["Refractory symptoms"],
        )

    def _atrial_fibrillation_protocol(self) -> TreatmentProtocol:
        """Atrial Fibrillation management protocol."""
        return TreatmentProtocol(
            diagnosis="Atrial Fibrillation",
            icd10_code="I48.9",
            first_line_drugs=[
                # Rate control (usually preferred)
                Medication(
                    drug_name="Metoprolol",
                    generic_name="Metoprolol",
                    strength="25mg",
                    form="tablet",
                    dose="1",
                    frequency="BD-TDS",
                    instructions="target HR 60-100 bpm",
                    indication="Rate control",
                ),
                Medication(
                    drug_name="Diltiazem",
                    generic_name="Diltiazem",
                    strength="60mg",
                    form="tablet",
                    dose="1",
                    frequency="TDS",
                    indication="Alternative rate control (if beta-blocker CI)",
                ),
                # Anticoagulation (based on CHA2DS2-VASc)
                Medication(
                    drug_name="Apixaban",
                    generic_name="Apixaban",
                    strength="5mg",
                    form="tablet",
                    dose="1",
                    frequency="BD",
                    duration="lifelong (if CHA2DS2-VASc ≥2)",
                    indication="NOAC - preferred over warfarin",
                ),
                Medication(
                    drug_name="Rivaroxaban",
                    generic_name="Rivaroxaban",
                    strength="20mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    instructions="with evening meal",
                    indication="Alternative NOAC",
                ),
            ],
            second_line_drugs=[
                # Rhythm control
                Medication(
                    drug_name="Amiodarone",
                    generic_name="Amiodarone",
                    strength="200mg",
                    form="tablet",
                    dose="3 tablets TDS x 1 week, then 1 OD",
                    frequency="variable",
                    indication="Rhythm control (if symptomatic)",
                ),
                # Warfarin (if NOACs not available/affordable)
                Medication(
                    drug_name="Warfarin",
                    generic_name="Warfarin",
                    strength="5mg",
                    form="tablet",
                    dose="variable",
                    frequency="OD",
                    instructions="target INR 2-3 (Indians: 2.0-2.5 safer)",
                    indication="Traditional anticoagulation",
                ),
            ],
            investigations=[
                "ECG (confirm AF)",
                "2D Echo (LA size, LV function, valves, thrombus)",
                "TSH (hyperthyroidism can cause AF)",
                "Renal function, CBC",
                "CHA2DS2-VASc score calculation",
                "HAS-BLED score",
            ],
            monitoring=[
                "HR and rhythm",
                "If on warfarin: INR monthly (target 2-3)",
                "If on NOAC: renal function q6-12 months",
                "Bleeding symptoms",
                "Stroke symptoms",
            ],
            lifestyle_advice=[
                "Avoid excessive alcohol",
                "Caffeine moderation",
                "Manage triggers (stress, sleep deprivation)",
                "Regular follow-up",
            ],
            follow_up_interval="2 weeks initially, then 3 monthly",
            referral_criteria=[
                "Symptomatic despite rate control",
                "Hemodynamic instability",
                "Consider ablation if young, symptomatic",
            ],
            contraindications={
                "noacs": ["Mechanical heart valve", "Severe renal impairment (Cr Cl <15)"],
                "warfarin": ["Active bleeding", "Pregnancy (teratogenic)"],
            },
        )

    def _hypertension_stage1_protocol(self) -> TreatmentProtocol:
        """Stage 1 Hypertension (140-159/90-99 mmHg) - India-specific."""
        return TreatmentProtocol(
            diagnosis="Stage 1 Hypertension (140-159/90-99)",
            icd10_code="I10",
            first_line_drugs=[
                # Indians respond better to CCB than ACE-I
                Medication(
                    drug_name="Amlodipine",
                    generic_name="Amlodipine",
                    strength="5mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    instructions="morning",
                    indication="CCB - first choice in Indians",
                ),
                Medication(
                    drug_name="Telmisartan",
                    generic_name="Telmisartan",
                    strength="40mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    indication="ARB - good for DM, CKD",
                ),
            ],
            second_line_drugs=[
                Medication(
                    drug_name="Chlorthalidone",
                    generic_name="Chlorthalidone",
                    strength="12.5mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    indication="Add if not controlled",
                ),
            ],
            investigations=[
                "ECG (LVH)",
                "2D Echo (if symptoms or abnormal ECG)",
                "Fundoscopy",
                "Urine albumin/creatinine ratio",
                "Serum creatinine, eGFR",
                "Lipid profile",
                "FBS/HbA1c",
            ],
            monitoring=[
                "BP every visit (target <140/90, <130/80 if DM/CKD)",
                "Home BP monitoring",
                "Kidney function yearly",
            ],
            lifestyle_advice=[
                "DASH diet - rich in fruits, vegetables",
                "Salt restriction <5g/day",
                "Weight loss if BMI >25",
                "Exercise 150 min/week",
                "Limit alcohol (<2 drinks/day men, <1 women)",
                "Smoking cessation",
            ],
            follow_up_interval="4 weeks",
            referral_criteria=[
                "BP >180/110 despite triple therapy",
                "Secondary hypertension suspected",
            ],
        )

    def _hypertension_stage2_protocol(self) -> TreatmentProtocol:
        """Stage 2 Hypertension (≥160/100 mmHg) - Combination therapy."""
        return TreatmentProtocol(
            diagnosis="Stage 2 Hypertension (≥160/100)",
            icd10_code="I10",
            first_line_drugs=[
                # Start with dual combination
                Medication(
                    drug_name="Amlodipine + Telmisartan",
                    generic_name="Amlodipine + Telmisartan",
                    strength="5mg/40mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    indication="Fixed-dose combination preferred",
                ),
                Medication(
                    drug_name="Chlorthalidone",
                    generic_name="Chlorthalidone",
                    strength="12.5mg",
                    form="tablet",
                    dose="1",
                    frequency="OD",
                    indication="Add thiazide for triple therapy",
                ),
            ],
            investigations=[
                "ECG, 2D Echo",
                "Fundoscopy",
                "Renal function, electrolytes",
                "Urine microalbumin",
                "Lipid profile, HbA1c",
                "Consider secondary causes workup",
            ],
            monitoring=["BP, kidney function, K+"],
            lifestyle_advice=[
                "Aggressive lifestyle modification",
                "Salt <5g/day",
                "DASH diet",
                "Weight loss",
            ],
            follow_up_interval="2 weeks",
            referral_criteria=["Resistant hypertension (>3 drugs)"],
        )

    def get_protocol(self, condition: str) -> Optional[TreatmentProtocol]:
        """
        Get cardiology protocol for a condition.

        Args:
            condition: Condition name (e.g., 'stemi', 'heart_failure')

        Returns:
            TreatmentProtocol if found, None otherwise
        """
        condition_key = condition.lower().replace(" ", "_")
        return self.protocols.get(condition_key)

    def check_compliance(
        self,
        prescription: Dict,
        condition: str,
    ) -> ComplianceReport:
        """
        Check prescription compliance with cardiology guidelines.

        Args:
            prescription: Dict with medications list
            condition: Cardiac condition being treated

        Returns:
            ComplianceReport with cardiology-specific checks
        """
        protocol = self.get_protocol(condition)
        if not protocol:
            return ComplianceReport(
                diagnosis=condition,
                is_compliant=True,
                suggestions=["No specific cardiology protocol found"],
                score=100.0,
            )

        issues = []
        score = 100.0
        prescribed_drugs = prescription.get("medications", [])
        prescribed_names = [m.get("drug_name", "").lower() for m in prescribed_drugs]

        # STEMI/NSTEMI: Check for DAPT
        if "stemi" in condition.lower() or "nstemi" in condition.lower():
            has_aspirin = any("aspirin" in name for name in prescribed_names)
            has_p2y12 = any(
                drug in name for drug in ["clopidogrel", "ticagrelor", "prasugrel"]
                for name in prescribed_names
            )

            if not has_aspirin:
                issues.append(
                    ComplianceIssue(
                        severity="critical",
                        category="drug_choice",
                        description="Aspirin not prescribed in ACS",
                        recommendation="Add Aspirin 150mg OD (lifelong)",
                    )
                )
                score -= 30

            if not has_p2y12:
                issues.append(
                    ComplianceIssue(
                        severity="critical",
                        category="drug_choice",
                        description="P2Y12 inhibitor not prescribed",
                        recommendation="Add Ticagrelor 90mg BD or Clopidogrel 75mg OD",
                    )
                )
                score -= 30

        # Heart Failure: Check for GDMT
        if "heart_failure" in condition.lower() or "hfref" in condition.lower():
            has_arni_or_acei = any(
                drug in name for drug in ["sacubitril", "ramipril", "enalapril", "lisinopril"]
                for name in prescribed_names
            )
            has_bb = any(
                drug in name for drug in ["metoprolol", "carvedilol", "bisoprolol"]
                for name in prescribed_names
            )
            has_mra = any("spironolactone" in name for name in prescribed_names)
            has_sglt2i = any(
                drug in name for drug in ["dapagliflozin", "empagliflozin"]
                for name in prescribed_names
            )

            if not has_arni_or_acei:
                issues.append(
                    ComplianceIssue(
                        severity="critical",
                        category="drug_choice",
                        description="ARNI/ACE-I not prescribed in HFrEF",
                        recommendation="Add Sacubitril/Valsartan or Ramipril",
                    )
                )
                score -= 20

            if not has_bb:
                issues.append(
                    ComplianceIssue(
                        severity="critical",
                        category="drug_choice",
                        description="Beta-blocker not prescribed",
                        recommendation="Add Carvedilol or Metoprolol",
                    )
                )
                score -= 20

            if not has_sglt2i:
                issues.append(
                    ComplianceIssue(
                        severity="warning",
                        category="drug_choice",
                        description="SGLT2i not prescribed (now part of GDMT)",
                        recommendation="Consider adding Dapagliflozin 10mg OD",
                    )
                )
                score -= 10

        return ComplianceReport(
            diagnosis=condition,
            is_compliant=score >= 70,
            issues=issues,
            score=max(0, score),
        )

    def get_red_flags(self, presentation: Dict) -> List[RedFlag]:
        """
        Identify cardiac red flags requiring immediate action.

        Args:
            presentation: Dict with symptoms, vitals, etc.

        Returns:
            List of RedFlag objects
        """
        red_flags = []

        # Chest pain red flags
        if "chest pain" in presentation.get("chief_complaint", "").lower():
            red_flags.append(
                RedFlag(
                    symptom="Chest pain",
                    urgency="EMERGENCY",
                    action="ECG within 10 minutes, troponin, cardiology consult",
                )
            )

        # Vitals
        bp_systolic = presentation.get("bp_systolic")
        if bp_systolic and bp_systolic > 180:
            red_flags.append(
                RedFlag(
                    symptom=f"Severe hypertension (SBP {bp_systolic})",
                    urgency="URGENT",
                    action="Rule out hypertensive emergency (ACS, CVA, aortic dissection)",
                )
            )

        heart_rate = presentation.get("pulse")
        if heart_rate and heart_rate > 120:
            red_flags.append(
                RedFlag(
                    symptom=f"Tachycardia (HR {heart_rate})",
                    urgency="URGENT",
                    action="ECG, check for AF, ACS, PE, sepsis",
                )
            )

        return red_flags

    def get_referral_criteria(self, condition: str) -> List[str]:
        """
        Get specialist referral criteria for cardiac conditions.

        Args:
            condition: Cardiac condition

        Returns:
            List of referral criteria
        """
        protocol = self.get_protocol(condition)
        if protocol:
            return protocol.referral_criteria
        return []
