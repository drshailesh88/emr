"""Medical Named Entity Recognition for Indian clinical context.

Extracts medical entities (symptoms, diagnoses, drugs, investigations, procedures)
with support for Indian medical terminology and abbreviations.
"""

import re
import json
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta

from .entities import (
    Symptom, Diagnosis, Drug, Investigation, Procedure,
    Severity, Onset
)


class MedicalNER:
    """Medical Named Entity Recognition with Indian clinical context."""

    # ICD-10 mapping for common Indian conditions
    ICD10_MAPPING = {
        "diabetes mellitus": "E11",
        "type 2 diabetes": "E11.9",
        "type 1 diabetes": "E10.9",
        "hypertension": "I10",
        "essential hypertension": "I10",
        "ischemic heart disease": "I25.9",
        "coronary artery disease": "I25.1",
        "heart failure": "I50.9",
        "acute myocardial infarction": "I21.9",
        "cerebrovascular accident": "I64",
        "stroke": "I64",
        "chronic kidney disease": "N18.9",
        "ckd": "N18.9",
        "copd": "J44.9",
        "chronic obstructive pulmonary disease": "J44.9",
        "asthma": "J45.9",
        "pneumonia": "J18.9",
        "tuberculosis": "A15.9",
        "pulmonary tuberculosis": "A15.0",
        "dengue": "A90",
        "malaria": "B54",
        "typhoid": "A01.0",
        "viral fever": "B34.9",
        "gastroenteritis": "K52.9",
        "peptic ulcer": "K27.9",
        "gerd": "K21.9",
        "cirrhosis": "K74.6",
        "hepatitis": "B19.9",
        "acute kidney injury": "N17.9",
        "urinary tract infection": "N39.0",
        "uti": "N39.0",
        "hypothyroidism": "E03.9",
        "hyperthyroidism": "E05.9",
        "anemia": "D64.9",
        "iron deficiency anemia": "D50.9",
        "rheumatoid arthritis": "M06.9",
        "osteoarthritis": "M19.9",
        "depression": "F32.9",
        "anxiety": "F41.9",
    }

    # Common Indian drug names (brand + generic)
    INDIAN_DRUGS = {
        # Diabetes
        "metformin": {"generic": "Metformin", "brands": ["Glycomet", "Obimet", "Glucophage"]},
        "glimepiride": {"generic": "Glimepiride", "brands": ["Amaryl", "Glemer"]},
        "insulin": {"generic": "Insulin", "brands": ["Mixtard", "Actrapid", "Lantus"]},

        # Hypertension
        "amlodipine": {"generic": "Amlodipine", "brands": ["Amlong", "Amlodac", "Stamlo"]},
        "telmisartan": {"generic": "Telmisartan", "brands": ["Telma", "Telsar"]},
        "atenolol": {"generic": "Atenolol", "brands": ["Aten", "Tenormin"]},
        "enalapril": {"generic": "Enalapril", "brands": ["Enam", "Envas"]},

        # Cardiac
        "aspirin": {"generic": "Aspirin", "brands": ["Ecosprin", "Loprin"]},
        "atorvastatin": {"generic": "Atorvastatin", "brands": ["Atorva", "Lipitor", "Storvas"]},
        "clopidogrel": {"generic": "Clopidogrel", "brands": ["Clopivas", "Plavix"]},

        # Antibiotics
        "amoxicillin": {"generic": "Amoxicillin", "brands": ["Mox", "Novamox"]},
        "azithromycin": {"generic": "Azithromycin", "brands": ["Azithral", "Azee"]},
        "ciprofloxacin": {"generic": "Ciprofloxacin", "brands": ["Ciplox", "Cifran"]},

        # Antipyretics
        "paracetamol": {"generic": "Paracetamol", "brands": ["Crocin", "Dolo", "Calpol"]},
        "ibuprofen": {"generic": "Ibuprofen", "brands": ["Brufen", "Combiflam"]},

        # GI
        "pantoprazole": {"generic": "Pantoprazole", "brands": ["Pan", "Pantocid"]},
        "omeprazole": {"generic": "Omeprazole", "brands": ["Omez", "Prilosec"]},
        "domperidone": {"generic": "Domperidone", "brands": ["Domstal", "Vomistop"]},
    }

    # Severity markers in Indian clinical notes
    SEVERITY_MARKERS = {
        Severity.MILD: ["mild", "slight", "minimal", "minor", "low grade"],
        Severity.MODERATE: ["moderate", "significant", "considerable"],
        Severity.SEVERE: ["severe", "intense", "marked", "high grade", "extreme"],
        Severity.CRITICAL: ["critical", "life-threatening", "very severe"],
    }

    # Onset markers
    ONSET_MARKERS = {
        Onset.ACUTE: ["acute", "sudden", "abrupt", "today", "this morning"],
        Onset.SUBACUTE: ["subacute", "few days", "recent"],
        Onset.CHRONIC: ["chronic", "long-standing", "since years", "since months"],
        Onset.GRADUAL: ["gradual", "progressive", "slowly"],
        Onset.SUDDEN: ["sudden", "sudden onset", "abruptly"],
    }

    # Common symptoms in Indian context
    SYMPTOM_DATABASE = {
        "fever": {"system": "general", "red_flags": ["high fever", "persistent fever"]},
        "chest pain": {"system": "cardiovascular", "red_flags": ["crushing", "radiating"]},
        "breathlessness": {"system": "respiratory", "red_flags": ["at rest", "severe"]},
        "cough": {"system": "respiratory", "red_flags": ["hemoptysis", "blood in sputum"]},
        "abdominal pain": {"system": "gastrointestinal", "red_flags": ["severe", "rigid abdomen"]},
        "headache": {"system": "neurological", "red_flags": ["worst headache", "sudden onset"]},
        "dizziness": {"system": "neurological", "red_flags": ["with syncope", "severe"]},
        "vomiting": {"system": "gastrointestinal", "red_flags": ["blood", "projectile"]},
        "diarrhea": {"system": "gastrointestinal", "red_flags": ["bloody", "severe dehydration"]},
        "weakness": {"system": "general", "red_flags": ["sudden", "one-sided"]},
        "palpitations": {"system": "cardiovascular", "red_flags": ["irregular", "with syncope"]},
        "syncope": {"system": "neurological", "red_flags": ["any syncope"]},
    }

    # Investigation categories
    INVESTIGATION_CATEGORIES = {
        "lab": [
            "CBC", "hemoglobin", "hb", "wbc", "platelet", "ESR",
            "creatinine", "urea", "BUN", "eGFR",
            "sodium", "potassium", "electrolytes",
            "blood sugar", "FBS", "RBS", "PPBS", "HbA1c",
            "LFT", "SGOT", "SGPT", "bilirubin", "albumin",
            "lipid profile", "cholesterol", "triglycerides", "HDL", "LDL",
            "TSH", "T3", "T4",
            "urine routine", "urine culture",
            "troponin", "CPK-MB", "BNP", "D-dimer",
        ],
        "imaging": [
            "X-ray", "chest X-ray", "CXR",
            "ultrasound", "USG", "sonography",
            "CT scan", "computed tomography",
            "MRI", "magnetic resonance",
            "echo", "echocardiography", "2D echo",
            "angiography", "coronary angiography",
        ],
        "procedure": [
            "ECG", "EKG", "electrocardiogram",
            "TMT", "treadmill test",
            "spirometry", "PFT",
            "endoscopy", "colonoscopy",
            "biopsy",
        ],
    }

    def __init__(self, llm_service=None):
        """Initialize NER with optional LLM service."""
        self.llm_service = llm_service

    def extract_symptoms(self, text: str) -> List[Symptom]:
        """
        Extract symptoms with duration, severity, and onset.

        Args:
            text: Clinical text to analyze

        Returns:
            List of Symptom objects
        """
        symptoms = []
        text_lower = text.lower()

        for symptom_name, info in self.SYMPTOM_DATABASE.items():
            # Check if symptom is mentioned
            pattern = r'\b' + re.escape(symptom_name) + r'\b'
            matches = re.finditer(pattern, text_lower)

            for match in matches:
                # Get context around symptom
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]

                symptom = Symptom(
                    name=symptom_name,
                    duration=self._extract_duration_from_context(context),
                    severity=self._extract_severity_from_context(context),
                    onset=self._extract_onset_from_context(context),
                    location=self._extract_location_from_context(symptom_name, context),
                    context=context,
                )

                symptoms.append(symptom)

        return symptoms

    def extract_diagnoses(self, text: str) -> List[Diagnosis]:
        """
        Extract diagnoses with ICD-10 mapping.

        Args:
            text: Clinical text to analyze

        Returns:
            List of Diagnosis objects
        """
        diagnoses = []
        text_lower = text.lower()

        # Look for diagnosis section
        diag_section = self._extract_diagnosis_section(text)
        if not diag_section:
            diag_section = text

        # Match against known diagnoses
        for diagnosis_name, icd10 in self.ICD10_MAPPING.items():
            pattern = r'\b' + re.escape(diagnosis_name) + r'\b'
            if re.search(pattern, diag_section.lower()):
                # Check if it's primary diagnosis
                is_primary = self._is_primary_diagnosis(diagnosis_name, diag_section)

                diagnoses.append(Diagnosis(
                    name=diagnosis_name.title(),
                    icd10_code=icd10,
                    is_primary=is_primary,
                    confidence=0.9 if is_primary else 0.7,
                    context=diag_section[:200],
                ))

        return diagnoses

    def extract_drugs(self, text: str) -> List[Drug]:
        """
        Extract medications with name, dose, route, frequency.

        Args:
            text: Clinical text to analyze

        Returns:
            List of Drug objects
        """
        drugs = []
        text_lower = text.lower()

        # Pattern 1: Tab. Drugname strength frequency
        pattern1 = r'(?:tab|tablet|cap|capsule|syrup|inj|injection)\.\s*([a-z]+(?:\s+[a-z]+)?)\s+([\d.]+\s*(?:mg|mcg|g|ml))'
        matches1 = re.finditer(pattern1, text_lower)

        for match in matches1:
            drug_name = match.group(1).strip()
            strength = match.group(2).strip()

            # Get context for frequency and duration
            context_start = max(0, match.start() - 20)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]

            # Extract frequency
            freq_pattern = r'\b(OD|BD|TDS|QID|HS|SOS|stat)\b'
            freq_match = re.search(freq_pattern, context, re.IGNORECASE)
            frequency = freq_match.group(1).upper() if freq_match else "OD"

            # Extract duration
            duration_pattern = r'(?:for|x)\s+(\d+)\s+(day|week|month)s?'
            duration_match = re.search(duration_pattern, context, re.IGNORECASE)
            duration = f"{duration_match.group(1)} {duration_match.group(2)}s" if duration_match else ""

            # Extract instructions
            instructions = ""
            if "before" in context.lower() or "ac" in context.lower():
                instructions = "before meals"
            elif "after" in context.lower() or "pc" in context.lower():
                instructions = "after meals"

            # Map to generic/brand
            generic, brand = self._map_drug_name(drug_name)

            drugs.append(Drug(
                name=drug_name.title(),
                generic_name=generic,
                brand_name=brand,
                strength=strength,
                dose="1",
                frequency=frequency,
                duration=duration,
                instructions=instructions,
                context=context,
            ))

        return drugs

    def extract_investigations(self, text: str) -> List[Investigation]:
        """
        Extract investigations/lab tests.

        Args:
            text: Clinical text to analyze

        Returns:
            List of Investigation objects
        """
        investigations = []
        text_lower = text.lower()

        # Check each investigation
        for category, inv_list in self.INVESTIGATION_CATEGORIES.items():
            for inv_name in inv_list:
                pattern = r'\b' + re.escape(inv_name.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    # Determine urgency
                    urgency = "routine"
                    if "stat" in text_lower or "urgent" in text_lower:
                        urgency = "urgent"
                    elif "emergency" in text_lower:
                        urgency = "stat"

                    investigations.append(Investigation(
                        name=inv_name.upper() if len(inv_name) <= 5 else inv_name.title(),
                        test_type=category,
                        urgency=urgency,
                        context=text[:200],
                    ))

        # Remove duplicates
        seen = set()
        unique_investigations = []
        for inv in investigations:
            if inv.name not in seen:
                seen.add(inv.name)
                unique_investigations.append(inv)

        return unique_investigations

    def extract_procedures(self, text: str) -> List[Procedure]:
        """
        Extract medical procedures.

        Args:
            text: Clinical text to analyze

        Returns:
            List of Procedure objects
        """
        procedures = []
        text_lower = text.lower()

        # Common procedures in Indian context
        procedure_keywords = {
            "PCI": "therapeutic",
            "PTCA": "therapeutic",
            "angioplasty": "therapeutic",
            "CABG": "surgical",
            "pacemaker": "therapeutic",
            "stenting": "therapeutic",
            "catheterization": "diagnostic",
            "endoscopy": "diagnostic",
            "colonoscopy": "diagnostic",
            "biopsy": "diagnostic",
            "dialysis": "therapeutic",
            "intubation": "therapeutic",
        }

        for proc_name, proc_type in procedure_keywords.items():
            pattern = r'\b' + re.escape(proc_name.lower()) + r'\b'
            if re.search(pattern, text_lower):
                # Extract date if mentioned
                date_pattern = r'(?:on|done on|performed on)\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
                date_match = re.search(date_pattern, text_lower)
                # Date parsing would go here

                procedures.append(Procedure(
                    name=proc_name.upper() if len(proc_name) <= 5 else proc_name.title(),
                    procedure_type=proc_type,
                    context=text[:200],
                ))

        return procedures

    # ========== Private Helper Methods ==========

    def _extract_duration_from_context(self, context: str) -> Optional[str]:
        """Extract duration from symptom context."""
        duration_pattern = r'(?:for|since|x|from)\s+(\d+)\s+(day|days|week|weeks|month|months|year|years|hour|hours)'
        match = re.search(duration_pattern, context, re.IGNORECASE)
        if match:
            num = match.group(1)
            unit = match.group(2).rstrip('s')  # Remove plural 's'
            return f"{num} {unit}{'s' if int(num) > 1 else ''}"
        return None

    def _extract_severity_from_context(self, context: str) -> Optional[Severity]:
        """Extract severity from context."""
        context_lower = context.lower()

        for severity, markers in self.SEVERITY_MARKERS.items():
            for marker in markers:
                if marker in context_lower:
                    return severity

        return None

    def _extract_onset_from_context(self, context: str) -> Optional[Onset]:
        """Extract onset pattern from context."""
        context_lower = context.lower()

        for onset, markers in self.ONSET_MARKERS.items():
            for marker in markers:
                if marker in context_lower:
                    return onset

        return None

    def _extract_location_from_context(self, symptom: str, context: str) -> Optional[str]:
        """Extract anatomical location for localized symptoms."""
        if "pain" not in symptom and "ache" not in symptom:
            return None

        location_keywords = [
            "chest", "abdomen", "head", "back", "leg", "arm",
            "epigastric", "substernal", "left", "right",
            "upper", "lower", "central"
        ]

        for location in location_keywords:
            if re.search(r'\b' + location + r'\b', context, re.IGNORECASE):
                return location

        return None

    def _extract_diagnosis_section(self, text: str) -> str:
        """Extract diagnosis/impression section from clinical note."""
        patterns = [
            r'(?:diagnosis|impression|assessment)[:\s]+((?:[^\n]+\n?)+)',
            r'(?:diagnosed with|impression of)[:\s]+([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return ""

    def _is_primary_diagnosis(self, diagnosis: str, text: str) -> bool:
        """Determine if diagnosis is primary (vs secondary)."""
        # Look for indicators
        primary_indicators = ["primary", "main", "principal"]
        text_lower = text.lower()

        # Check if diagnosis appears near primary indicators
        for indicator in primary_indicators:
            if indicator in text_lower and diagnosis in text_lower:
                return True

        # If it's the first diagnosis mentioned, it's likely primary
        diag_section = self._extract_diagnosis_section(text)
        if diag_section.lower().find(diagnosis) < 50:
            return True

        return False

    def _map_drug_name(self, drug_name: str) -> tuple[Optional[str], Optional[str]]:
        """Map drug name to generic and brand."""
        drug_lower = drug_name.lower()

        # Check if it's a known generic
        if drug_lower in self.INDIAN_DRUGS:
            info = self.INDIAN_DRUGS[drug_lower]
            return info["generic"], None

        # Check if it's a known brand
        for generic, info in self.INDIAN_DRUGS.items():
            if drug_name.title() in info["brands"]:
                return info["generic"], drug_name.title()

        return None, None
