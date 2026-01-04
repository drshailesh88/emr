"""Clinical reasoning engine with India-specific disease prevalence.

Generates differential diagnoses, suggests investigations, flags red flags,
and provides clinical summaries using Bayesian reasoning and LLM augmentation.
"""

import json
from typing import List, Dict, Optional
from dataclasses import asdict

from .entities import (
    Symptom, Diagnosis, Investigation, Differential, RedFlag,
    SOAPNote, ClinicalContext, Severity
)


class ClinicalReasoning:
    """Clinical reasoning with India-specific disease prevalence."""

    # India-specific disease prevalence (rough estimates for Bayesian priors)
    # These are population prevalence rates
    INDIA_PREVALENCE = {
        # High prevalence in India
        "diabetes mellitus": 0.08,  # 8% of adult population
        "hypertension": 0.25,  # 25% of adults
        "tuberculosis": 0.002,  # 200 per 100,000
        "dengue": 0.001,  # Seasonal, varies by region
        "malaria": 0.0005,  # Varies by region
        "typhoid": 0.0003,
        "viral fever": 0.05,  # Common
        "gastroenteritis": 0.03,
        "respiratory tract infection": 0.04,
        "urinary tract infection": 0.02,

        # Moderate prevalence
        "ischemic heart disease": 0.06,
        "chronic kidney disease": 0.03,
        "copd": 0.04,
        "asthma": 0.03,
        "cirrhosis": 0.01,
        "hepatitis": 0.02,

        # Lower prevalence but important
        "acute coronary syndrome": 0.0003,
        "stroke": 0.0015,
        "heart failure": 0.02,
        "acute kidney injury": 0.001,
        "sepsis": 0.0005,
    }

    # Symptom-diagnosis associations (simplified Bayesian network)
    # Format: symptom -> {diagnosis: likelihood_ratio}
    SYMPTOM_DIAGNOSIS_MAP = {
        "fever": {
            "viral fever": 5.0,
            "dengue": 3.0,
            "malaria": 3.0,
            "typhoid": 3.0,
            "tuberculosis": 2.0,
            "pneumonia": 3.0,
            "urinary tract infection": 2.0,
            "sepsis": 4.0,
        },
        "chest pain": {
            "acute coronary syndrome": 10.0,
            "angina": 8.0,
            "ischemic heart disease": 5.0,
            "gerd": 3.0,
            "costochondritis": 2.0,
        },
        "breathlessness": {
            "heart failure": 8.0,
            "acute coronary syndrome": 6.0,
            "copd": 6.0,
            "asthma": 6.0,
            "pneumonia": 5.0,
            "pulmonary embolism": 7.0,
        },
        "cough": {
            "respiratory tract infection": 5.0,
            "tuberculosis": 4.0,
            "copd": 4.0,
            "asthma": 3.0,
            "pneumonia": 5.0,
            "heart failure": 2.0,
        },
        "abdominal pain": {
            "gastroenteritis": 5.0,
            "peptic ulcer": 4.0,
            "appendicitis": 3.0,
            "cholecystitis": 3.0,
            "pancreatitis": 3.0,
        },
        "headache": {
            "migraine": 4.0,
            "tension headache": 5.0,
            "dengue": 3.0,
            "malaria": 2.0,
            "stroke": 2.0,
            "meningitis": 4.0,
        },
        "diarrhea": {
            "gastroenteritis": 8.0,
            "food poisoning": 6.0,
            "cholera": 3.0,
            "typhoid": 4.0,
        },
        "vomiting": {
            "gastroenteritis": 7.0,
            "food poisoning": 6.0,
            "appendicitis": 3.0,
            "pancreatitis": 4.0,
            "dengue": 3.0,
        },
        "weakness": {
            "anemia": 5.0,
            "diabetes mellitus": 3.0,
            "hypothyroidism": 3.0,
            "stroke": 8.0,
            "sepsis": 4.0,
        },
        "syncope": {
            "cardiac arrhythmia": 8.0,
            "vasovagal syncope": 5.0,
            "acute coronary syndrome": 6.0,
            "stroke": 5.0,
        },
    }

    # Red flag patterns
    RED_FLAGS = {
        "cardiac": {
            "patterns": [
                "crushing chest pain",
                "radiating to jaw",
                "radiating to arm",
                "chest pain with sweating",
                "chest pain with breathlessness",
                "syncope with chest pain",
            ],
            "severity": Severity.CRITICAL,
            "action": "Emergency ECG, Troponin, immediate cardiology referral",
        },
        "neuro": {
            "patterns": [
                "sudden severe headache",
                "worst headache of life",
                "weakness one side",
                "facial deviation",
                "slurred speech",
                "loss of consciousness",
                "seizure",
                "confusion",
            ],
            "severity": Severity.CRITICAL,
            "action": "Emergency CT brain, immediate neurology referral",
        },
        "sepsis": {
            "patterns": [
                "fever with altered sensorium",
                "hypotension with fever",
                "tachycardia with fever",
                "rigors",
                "severe weakness with fever",
            ],
            "severity": Severity.CRITICAL,
            "action": "Blood culture, broad spectrum antibiotics, ICU referral",
        },
        "respiratory": {
            "patterns": [
                "breathlessness at rest",
                "severe breathlessness",
                "spo2 less than 90",
                "cyanosis",
                "unable to speak",
            ],
            "severity": Severity.CRITICAL,
            "action": "Oxygen therapy, ABG, chest X-ray, immediate referral",
        },
        "hemorrhage": {
            "patterns": [
                "hematemesis",
                "melena",
                "hemoptysis",
                "bleeding",
                "severe bleeding",
            ],
            "severity": Severity.CRITICAL,
            "action": "Hemoglobin, coagulation profile, immediate referral",
        },
        "abdominal": {
            "patterns": [
                "rigid abdomen",
                "guarding",
                "severe abdominal pain",
                "rebound tenderness",
            ],
            "severity": Severity.CRITICAL,
            "action": "Surgical consult, imaging, nil per oral",
        },
    }

    # Investigation protocols for common presentations
    INVESTIGATION_PROTOCOLS = {
        "chest pain": [
            "ECG (stat)",
            "Troponin I",
            "CK-MB",
            "Chest X-ray",
            "2D Echo",
        ],
        "fever": [
            "CBC with differential",
            "Malaria card test",
            "Dengue NS1 antigen",
            "Typhoid IgM",
            "Blood culture",
            "Urine routine",
            "Chest X-ray",
        ],
        "breathlessness": [
            "SpO2 monitoring",
            "Chest X-ray",
            "ECG",
            "2D Echo",
            "BNP/NT-proBNP",
            "ABG",
        ],
        "diabetes screening": [
            "Fasting blood sugar",
            "HbA1c",
            "Lipid profile",
            "Creatinine",
            "Urine microalbumin",
            "Fundoscopy",
        ],
        "hypertension workup": [
            "ECG",
            "Creatinine",
            "Electrolytes",
            "Lipid profile",
            "Urine routine",
            "2D Echo",
        ],
        "anemia workup": [
            "CBC",
            "Peripheral smear",
            "Iron studies",
            "Vitamin B12",
            "Folate",
            "Reticulocyte count",
        ],
    }

    def __init__(self, llm_service=None):
        """Initialize clinical reasoning engine."""
        self.llm_service = llm_service

    def generate_differentials(
        self,
        symptoms: List[Symptom],
        patient_context: Optional[ClinicalContext] = None
    ) -> List[Differential]:
        """
        Generate ranked differential diagnoses using Bayesian reasoning.

        Args:
            symptoms: List of patient symptoms
            patient_context: Patient's clinical context (age, comorbidities, etc.)

        Returns:
            List of Differential diagnoses ranked by probability
        """
        if not symptoms:
            return []

        # Collect all potential diagnoses from symptoms
        candidate_diagnoses: Dict[str, Dict] = {}

        for symptom in symptoms:
            symptom_name = symptom.name.lower()

            if symptom_name in self.SYMPTOM_DIAGNOSIS_MAP:
                for diagnosis, likelihood_ratio in self.SYMPTOM_DIAGNOSIS_MAP[symptom_name].items():
                    if diagnosis not in candidate_diagnoses:
                        candidate_diagnoses[diagnosis] = {
                            "likelihood_ratios": [],
                            "supporting_features": [],
                        }

                    candidate_diagnoses[diagnosis]["likelihood_ratios"].append(likelihood_ratio)
                    candidate_diagnoses[diagnosis]["supporting_features"].append(symptom_name)

        # Calculate posterior probabilities using Bayes' theorem
        differentials = []

        for diagnosis, data in candidate_diagnoses.items():
            # Get prior probability (prevalence in India)
            prior = self.INDIA_PREVALENCE.get(diagnosis, 0.001)

            # Calculate combined likelihood ratio
            combined_lr = 1.0
            for lr in data["likelihood_ratios"]:
                combined_lr *= lr

            # Bayesian update: posterior odds = prior odds × likelihood ratio
            prior_odds = prior / (1 - prior)
            posterior_odds = prior_odds * combined_lr
            posterior_prob = posterior_odds / (1 + posterior_odds)

            # Adjust based on patient context
            if patient_context:
                posterior_prob = self._adjust_for_context(
                    diagnosis, posterior_prob, patient_context
                )

            # Get recommended investigations
            recommended_invs = self._get_investigations_for_diagnosis(diagnosis)

            # Check for red flags
            red_flags = self._get_red_flags_for_diagnosis(diagnosis, symptoms)

            differentials.append(Differential(
                diagnosis=diagnosis.title(),
                probability=min(posterior_prob, 0.95),  # Cap at 95%
                prior_probability=prior,
                supporting_features=data["supporting_features"],
                recommended_investigations=recommended_invs,
                red_flags=red_flags,
                treatment_urgency=self._determine_urgency(diagnosis, symptoms),
            ))

        # Sort by probability
        differentials.sort(key=lambda x: x.probability, reverse=True)

        # Use LLM to refine if available
        if self.llm_service and len(differentials) > 0:
            differentials = self._refine_differentials_with_llm(
                symptoms, differentials, patient_context
            )

        return differentials[:10]  # Return top 10

    def suggest_investigations(
        self,
        differentials: List[Differential]
    ) -> List[Investigation]:
        """
        Suggest investigations to rule in/out differential diagnoses.

        Args:
            differentials: List of differential diagnoses

        Returns:
            Prioritized list of investigations
        """
        investigations = []
        seen = set()

        # Add investigations from each differential (weighted by probability)
        for diff in differentials:
            for inv_name in diff.recommended_investigations:
                if inv_name not in seen:
                    seen.add(inv_name)

                    # Determine urgency based on differential probability and urgency
                    urgency = "routine"
                    if diff.treatment_urgency == "stat" or diff.probability > 0.7:
                        urgency = "urgent"
                    if diff.treatment_urgency == "stat" and diff.probability > 0.8:
                        urgency = "stat"

                    # Determine test type
                    test_type = self._categorize_investigation(inv_name)

                    investigations.append(Investigation(
                        name=inv_name,
                        test_type=test_type,
                        urgency=urgency,
                        reason=f"R/O {diff.diagnosis}",
                    ))

        return investigations

    def flag_red_flags(self, presentation: Dict) -> List[RedFlag]:
        """
        Identify red flags requiring immediate attention.

        Args:
            presentation: Dictionary with clinical presentation
                {
                    "symptoms": List[Symptom],
                    "vitals": Dict[str, str],
                    "history": str,
                }

        Returns:
            List of identified red flags
        """
        red_flags = []
        symptoms = presentation.get("symptoms", [])
        vitals = presentation.get("vitals", {})
        history = presentation.get("history", "").lower()

        # Check for red flag patterns
        for category, info in self.RED_FLAGS.items():
            for pattern in info["patterns"]:
                # Check in symptoms
                for symptom in symptoms:
                    if pattern.lower() in symptom.name.lower():
                        red_flags.append(RedFlag(
                            category=category,
                            description=pattern,
                            severity=info["severity"],
                            action_required=info["action"],
                            time_critical=True,
                            system=self._get_system_from_category(category),
                        ))

                # Check in history
                if pattern in history:
                    red_flags.append(RedFlag(
                        category=category,
                        description=pattern,
                        severity=info["severity"],
                        action_required=info["action"],
                        time_critical=True,
                        system=self._get_system_from_category(category),
                    ))

        # Check vital signs for red flags
        red_flags.extend(self._check_vital_red_flags(vitals))

        # Remove duplicates
        unique_flags = []
        seen_descriptions = set()
        for flag in red_flags:
            if flag.description not in seen_descriptions:
                seen_descriptions.add(flag.description)
                unique_flags.append(flag)

        return unique_flags

    def generate_clinical_summary(self, soap: SOAPNote) -> str:
        """
        Generate natural language clinical summary.

        Args:
            soap: Structured SOAP note

        Returns:
            Natural language summary
        """
        summary_parts = []

        # Chief complaint and duration
        if soap.chief_complaint:
            duration_text = f"for {soap.duration}" if soap.duration else ""
            summary_parts.append(
                f"Patient presents with {soap.chief_complaint} {duration_text}."
            )

        # Associated symptoms
        if soap.associated_symptoms:
            symptoms_text = ", ".join(soap.associated_symptoms[:3])
            summary_parts.append(f"Associated with {symptoms_text}.")

        # Vitals
        if soap.vitals:
            vital_strings = [f"{k}: {v}" for k, v in soap.vitals.items()]
            summary_parts.append(f"Vitals: {', '.join(vital_strings)}.")

        # Examination findings
        if soap.significant_findings:
            findings_text = "; ".join(soap.significant_findings[:2])
            summary_parts.append(f"Examination: {findings_text}.")

        # Assessment
        if soap.diagnoses:
            primary_diagnosis = soap.diagnoses[0]
            summary_parts.append(f"Impression: {primary_diagnosis}.")

        # Plan
        plan_items = []
        if soap.medications:
            plan_items.append(f"{len(soap.medications)} medications prescribed")
        if soap.investigations:
            inv_names = [inv.name for inv in soap.investigations[:3]]
            plan_items.append(f"Investigations: {', '.join(inv_names)}")
        if soap.follow_up:
            plan_items.append(f"Follow-up: {soap.follow_up}")

        if plan_items:
            summary_parts.append(f"Plan: {'; '.join(plan_items)}.")

        # Use LLM to create more natural summary if available
        if self.llm_service:
            summary = self._enhance_summary_with_llm(soap, " ".join(summary_parts))
            if summary:
                return summary

        return " ".join(summary_parts)

    # ========== Private Helper Methods ==========

    def _adjust_for_context(
        self,
        diagnosis: str,
        probability: float,
        context: ClinicalContext
    ) -> float:
        """Adjust probability based on patient context."""
        adjusted = probability

        # Age-based adjustments
        if context.patient_age:
            if diagnosis == "acute coronary syndrome" and context.patient_age > 50:
                adjusted *= 1.5
            elif diagnosis == "viral fever" and context.patient_age < 15:
                adjusted *= 1.3

        # Known conditions
        if context.known_conditions:
            conditions_lower = [c.lower() for c in context.known_conditions]

            if diagnosis == "acute coronary syndrome" and "diabetes" in " ".join(conditions_lower):
                adjusted *= 1.4
            if diagnosis == "heart failure" and "hypertension" in " ".join(conditions_lower):
                adjusted *= 1.3

        return min(adjusted, 0.95)

    def _get_investigations_for_diagnosis(self, diagnosis: str) -> List[str]:
        """Get recommended investigations for a diagnosis."""
        # Map diagnosis to investigation protocol
        protocol_map = {
            "acute coronary syndrome": "chest pain",
            "angina": "chest pain",
            "dengue": "fever",
            "malaria": "fever",
            "typhoid": "fever",
            "pneumonia": "fever",
            "heart failure": "breathlessness",
            "copd": "breathlessness",
            "asthma": "breathlessness",
        }

        protocol = protocol_map.get(diagnosis)
        if protocol and protocol in self.INVESTIGATION_PROTOCOLS:
            return self.INVESTIGATION_PROTOCOLS[protocol]

        return []

    def _get_red_flags_for_diagnosis(
        self,
        diagnosis: str,
        symptoms: List[Symptom]
    ) -> List[str]:
        """Get red flags for specific diagnosis."""
        red_flags = []

        if diagnosis in ["acute coronary syndrome", "angina"]:
            red_flags.append("Chest pain radiating to jaw/arm")
            red_flags.append("Chest pain with sweating")

        if diagnosis in ["stroke", "cerebrovascular accident"]:
            red_flags.append("Sudden neurological deficit")
            red_flags.append("Facial deviation or slurred speech")

        if diagnosis == "sepsis":
            red_flags.append("Altered sensorium with fever")
            red_flags.append("Hypotension")

        return red_flags

    def _determine_urgency(self, diagnosis: str, symptoms: List[Symptom]) -> str:
        """Determine treatment urgency for diagnosis."""
        critical_diagnoses = [
            "acute coronary syndrome", "stroke", "sepsis",
            "pulmonary embolism", "acute kidney injury"
        ]

        if diagnosis in critical_diagnoses:
            return "stat"

        # Check symptom severity
        for symptom in symptoms:
            if symptom.severity == Severity.CRITICAL:
                return "urgent"

        return "routine"

    def _categorize_investigation(self, inv_name: str) -> str:
        """Categorize investigation type."""
        inv_lower = inv_name.lower()

        imaging_keywords = ["x-ray", "ct", "mri", "ultrasound", "echo", "angiography"]
        if any(kw in inv_lower for kw in imaging_keywords):
            return "imaging"

        procedure_keywords = ["ecg", "tmt", "endoscopy", "biopsy"]
        if any(kw in inv_lower for kw in procedure_keywords):
            return "procedure"

        return "lab"

    def _get_system_from_category(self, category: str) -> str:
        """Map red flag category to body system."""
        system_map = {
            "cardiac": "cardiovascular",
            "neuro": "neurological",
            "sepsis": "systemic",
            "respiratory": "respiratory",
            "hemorrhage": "hematological",
            "abdominal": "gastrointestinal",
        }
        return system_map.get(category, "general")

    def _check_vital_red_flags(self, vitals: Dict[str, str]) -> List[RedFlag]:
        """Check vital signs for red flags."""
        red_flags = []

        # Parse BP
        if "BP" in vitals or "Blood Pressure" in vitals:
            bp_str = vitals.get("BP") or vitals.get("Blood Pressure", "")
            bp_match = re.match(r"(\d+)/(\d+)", bp_str)
            if bp_match:
                systolic = int(bp_match.group(1))
                diastolic = int(bp_match.group(2))

                if systolic > 180 or diastolic > 110:
                    red_flags.append(RedFlag(
                        category="hypertensive crisis",
                        description=f"Severely elevated BP: {bp_str}",
                        severity=Severity.CRITICAL,
                        action_required="Immediate BP management, rule out end-organ damage",
                        time_critical=True,
                        system="cardiovascular",
                    ))
                elif systolic < 90:
                    red_flags.append(RedFlag(
                        category="hypotension",
                        description=f"Hypotension: {bp_str}",
                        severity=Severity.SEVERE,
                        action_required="Rule out shock, fluid resuscitation",
                        time_critical=True,
                        system="cardiovascular",
                    ))

        # Parse SpO2
        if "SpO2" in vitals:
            spo2_str = vitals["SpO2"].rstrip('%')
            try:
                spo2 = int(spo2_str)
                if spo2 < 90:
                    red_flags.append(RedFlag(
                        category="hypoxia",
                        description=f"Low oxygen saturation: {spo2}%",
                        severity=Severity.CRITICAL,
                        action_required="Oxygen therapy, ABG, chest X-ray",
                        time_critical=True,
                        system="respiratory",
                    ))
            except:
                pass

        return red_flags

    def _refine_differentials_with_llm(
        self,
        symptoms: List[Symptom],
        differentials: List[Differential],
        context: Optional[ClinicalContext]
    ) -> List[Differential]:
        """Use LLM to refine differential diagnoses."""
        # TODO: Implement LLM-based refinement
        # This would send the top differentials to LLM for clinical reasoning
        return differentials

    def _enhance_summary_with_llm(self, soap: SOAPNote, basic_summary: str) -> Optional[str]:
        """Use LLM to create more natural clinical summary."""
        if not self.llm_service or not self.llm_service.is_available():
            return None

        prompt = f"""Generate a concise clinical summary from this SOAP note.

SOAP Note:
- Chief Complaint: {soap.chief_complaint}
- Duration: {soap.duration or 'Not specified'}
- Vitals: {', '.join(f'{k}: {v}' for k, v in soap.vitals.items())}
- Diagnoses: {', '.join(soap.diagnoses)}
- Medications: {len(soap.medications)} prescribed
- Investigations: {', '.join(inv.name for inv in soap.investigations[:5])}

Create a 2-3 sentence clinical summary suitable for a medical note."""

        success, response = self.llm_service.generate(prompt, json_mode=False, max_tokens=200)
        if success:
            return response.strip()

        return None


# Import re for vitals parsing
import re
