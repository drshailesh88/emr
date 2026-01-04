"""Clinical note extraction from natural language transcripts.

Handles Hindi, English, and code-mixed speech common in Indian healthcare.
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ...models.schemas import Medication, Vitals
from .entities import (
    SOAPNote, Drug, Investigation, Procedure, VitalSign,
    Severity, Onset, Symptom
)


class ClinicalNoteExtractor:
    """Extract structured clinical data from natural language transcripts."""

    # Common Indian medical abbreviations
    ABBREVIATIONS = {
        "c/o": "complains of",
        "h/o": "history of",
        "s/o": "suggestive of",
        "k/c/o": "known case of",
        "p/o": "per oral",
        "BP": "blood pressure",
        "PR": "pulse rate",
        "RR": "respiratory rate",
        "HR": "heart rate",
        "temp": "temperature",
        "wt": "weight",
        "ht": "height",
        "DM": "diabetes mellitus",
        "HTN": "hypertension",
        "IHD": "ischemic heart disease",
        "CAD": "coronary artery disease",
        "CVA": "cerebrovascular accident",
        "CKD": "chronic kidney disease",
        "COPD": "chronic obstructive pulmonary disease",
        "TB": "tuberculosis",
        "OD": "once daily",
        "BD": "twice daily",
        "TDS": "thrice daily",
        "QID": "four times daily",
        "HS": "at bedtime",
        "SOS": "as needed",
        "stat": "immediately",
        "AC": "before meals",
        "PC": "after meals",
        "IM": "intramuscular",
        "IV": "intravenous",
        "SC": "subcutaneous",
    }

    # Common Hinglish medical terms
    HINGLISH_TERMS = {
        "bukhar": "fever",
        "dard": "pain",
        "khasi": "cough",
        "saans": "breathing",
        "ulti": "vomiting",
        "dast": "diarrhea",
        "chakkar": "dizziness",
        "kamzori": "weakness",
        "pet dard": "abdominal pain",
        "sir dard": "headache",
        "seene mein dard": "chest pain",
        "pet kharab": "upset stomach",
        "gas": "flatulence",
        "acidity": "acidity",
        "neend nahi aati": "insomnia",
    }

    # Vital signs patterns (flexible for Indian style documentation)
    VITAL_PATTERNS = {
        "bp": r"(?:BP|blood pressure|bp)\s*[:-]?\s*(\d{2,3})\s*/\s*(\d{2,3})",
        "pulse": r"(?:PR|pulse|HR|heart rate)\s*[:-]?\s*(\d{2,3})",
        "temp": r"(?:temp|temperature)\s*[:-]?\s*([\d.]+)\s*(?:°F|F|fahrenheit)?",
        "spo2": r"(?:SpO2|spo2|oxygen|O2 sat)\s*[:-]?\s*(\d{2,3})\s*%?",
        "rr": r"(?:RR|respiratory rate)\s*[:-]?\s*(\d{1,2})",
        "weight": r"(?:wt|weight)\s*[:-]?\s*([\d.]+)\s*(?:kg|kgs)?",
        "height": r"(?:ht|height)\s*[:-]?\s*([\d.]+)\s*(?:cm|ft)?",
        "bmi": r"(?:BMI|bmi)\s*[:-]?\s*([\d.]+)",
        "sugar": r"(?:RBS|FBS|PPBS|blood sugar|sugar)\s*[:-]?\s*([\d.]+)",
    }

    # Duration patterns
    DURATION_PATTERN = r"(?:for|since|x|from)\s+(\d+)\s+(day|days|week|weeks|month|months|year|years|hour|hours|minute|minutes)"

    # Frequency patterns (Indian style)
    FREQUENCY_PATTERN = r"\b(OD|BD|TDS|QID|HS|SOS|stat|once daily|twice daily|thrice daily|four times daily|at bedtime|as needed)\b"

    def __init__(self, llm_service=None):
        """Initialize extractor with optional LLM service for complex extraction."""
        self.llm_service = llm_service

    def extract_soap_note(self, transcript: str) -> SOAPNote:
        """
        Extract structured SOAP note from natural speech.

        Args:
            transcript: Raw clinical notes (may be Hinglish)

        Returns:
            Structured SOAPNote object
        """
        # Normalize text
        normalized = self._normalize_text(transcript)

        # Extract components
        chief_complaint = self._extract_chief_complaint(normalized)
        vitals = self._extract_vitals_dict(normalized)
        examination = self._extract_examination(normalized)
        diagnoses = self._extract_diagnosis_list(normalized)
        medications = self._extract_medications(normalized)
        investigations = self._extract_investigations(normalized)

        # Build SOAP note
        soap = SOAPNote(
            chief_complaint=chief_complaint,
            history_of_present_illness=self._extract_history(normalized),
            associated_symptoms=self._extract_associated_symptoms(normalized),
            duration=self._extract_duration(normalized),
            vitals=vitals,
            examination_findings=examination,
            diagnoses=diagnoses,
            medications=medications,
            investigations=investigations,
            advice=self._extract_advice(normalized),
            follow_up=self._extract_follow_up(normalized),
            raw_transcript=transcript,
            extracted_at=datetime.now(),
        )

        # Use LLM for complex extraction if available
        if self.llm_service:
            soap = self._enhance_with_llm(soap, transcript)

        return soap

    def extract_vitals(self, transcript: str) -> Vitals:
        """
        Extract vital signs into Vitals schema.

        Args:
            transcript: Text containing vital signs

        Returns:
            Vitals object with extracted values
        """
        normalized = transcript.lower()
        vitals = Vitals(patient_id=0, recorded_at=datetime.now())

        # Extract BP
        bp_match = re.search(self.VITAL_PATTERNS["bp"], normalized, re.IGNORECASE)
        if bp_match:
            vitals.bp_systolic = int(bp_match.group(1))
            vitals.bp_diastolic = int(bp_match.group(2))

        # Extract pulse
        pulse_match = re.search(self.VITAL_PATTERNS["pulse"], normalized, re.IGNORECASE)
        if pulse_match:
            vitals.pulse = int(pulse_match.group(1))

        # Extract temperature (convert to Celsius if needed)
        temp_match = re.search(self.VITAL_PATTERNS["temp"], normalized, re.IGNORECASE)
        if temp_match:
            temp = float(temp_match.group(1))
            # Convert F to C if > 50 (likely Fahrenheit)
            if temp > 50:
                temp = (temp - 32) * 5 / 9
            vitals.temperature = round(temp, 1)

        # Extract SpO2
        spo2_match = re.search(self.VITAL_PATTERNS["spo2"], normalized, re.IGNORECASE)
        if spo2_match:
            vitals.spo2 = int(spo2_match.group(1))

        # Extract respiratory rate
        rr_match = re.search(self.VITAL_PATTERNS["rr"], normalized, re.IGNORECASE)
        if rr_match:
            vitals.respiratory_rate = int(rr_match.group(1))

        # Extract weight
        wt_match = re.search(self.VITAL_PATTERNS["weight"], normalized, re.IGNORECASE)
        if wt_match:
            vitals.weight = float(wt_match.group(1))

        # Extract height
        ht_match = re.search(self.VITAL_PATTERNS["height"], normalized, re.IGNORECASE)
        if ht_match:
            vitals.height = float(ht_match.group(1))

        # Calculate BMI if both weight and height available
        if vitals.weight and vitals.height:
            height_m = vitals.height / 100  # Convert cm to m
            vitals.bmi = round(vitals.weight / (height_m ** 2), 1)

        # Extract blood sugar
        sugar_match = re.search(self.VITAL_PATTERNS["sugar"], normalized, re.IGNORECASE)
        if sugar_match:
            vitals.blood_sugar = float(sugar_match.group(1))
            # Detect sugar type from context
            if "fbs" in normalized or "fasting" in normalized:
                vitals.sugar_type = "FBS"
            elif "ppbs" in normalized or "post" in normalized:
                vitals.sugar_type = "PPBS"
            else:
                vitals.sugar_type = "RBS"

        return vitals

    def extract_medications(self, transcript: str) -> List[Medication]:
        """
        Extract medications with dosing from transcript.

        Args:
            transcript: Text containing medication information

        Returns:
            List of Medication objects
        """
        medications = []
        normalized = self._normalize_text(transcript)

        # Common drug patterns (Indian brands and generics)
        drug_patterns = [
            r"(?:Tab|Tablet|Cap|Capsule|Syrup|Inj|Injection)\.\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+([\d.]+\s*(?:mg|mcg|g|ml))",
            r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+([\d.]+\s*(?:mg|mcg|g|ml))\s+(?:tab|cap|syrup)",
        ]

        for pattern in drug_patterns:
            matches = re.finditer(pattern, transcript, re.IGNORECASE)
            for match in matches:
                drug_name = match.group(1).strip()
                strength = match.group(2).strip()

                # Extract frequency from nearby text
                context = transcript[max(0, match.start() - 50):min(len(transcript), match.end() + 50)]
                freq_match = re.search(self.FREQUENCY_PATTERN, context, re.IGNORECASE)
                frequency = freq_match.group(1) if freq_match else "OD"

                # Extract duration
                duration_match = re.search(self.DURATION_PATTERN, context, re.IGNORECASE)
                duration = f"{duration_match.group(1)} {duration_match.group(2)}" if duration_match else "7 days"

                # Extract instructions
                instructions = ""
                if "before" in context.lower() or "ac" in context.lower():
                    instructions = "before meals"
                elif "after" in context.lower() or "pc" in context.lower():
                    instructions = "after meals"

                medications.append(Medication(
                    drug_name=drug_name,
                    strength=strength,
                    frequency=frequency,
                    duration=duration,
                    instructions=instructions
                ))

        # Use LLM for better extraction if available
        if self.llm_service and not medications:
            medications = self._extract_medications_with_llm(transcript)

        return medications

    # ========== Private Helper Methods ==========

    def _normalize_text(self, text: str) -> str:
        """Normalize Hinglish text to English."""
        normalized = text.lower()

        # Expand abbreviations
        for abbr, full in self.ABBREVIATIONS.items():
            normalized = re.sub(r'\b' + re.escape(abbr) + r'\b', full, normalized, flags=re.IGNORECASE)

        # Translate common Hinglish terms
        for hindi, english in self.HINGLISH_TERMS.items():
            normalized = re.sub(r'\b' + re.escape(hindi) + r'\b', english, normalized, flags=re.IGNORECASE)

        return normalized

    def _extract_chief_complaint(self, text: str) -> str:
        """Extract chief complaint from text."""
        # Look for c/o pattern
        complaint_patterns = [
            r"complains of\s+([^.]+)",
            r"presented with\s+([^.]+)",
            r"chief complaint[:\s]+([^.]+)",
        ]

        for pattern in complaint_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback: first sentence
        sentences = text.split('.')
        return sentences[0].strip() if sentences else ""

    def _extract_vitals_dict(self, text: str) -> Dict[str, str]:
        """Extract vitals as dictionary."""
        vitals_obj = self.extract_vitals(text)
        vitals_dict = {}

        if vitals_obj.bp_systolic and vitals_obj.bp_diastolic:
            vitals_dict["BP"] = f"{vitals_obj.bp_systolic}/{vitals_obj.bp_diastolic}"
        if vitals_obj.pulse:
            vitals_dict["Pulse"] = f"{vitals_obj.pulse} bpm"
        if vitals_obj.temperature:
            vitals_dict["Temperature"] = f"{vitals_obj.temperature}°C"
        if vitals_obj.spo2:
            vitals_dict["SpO2"] = f"{vitals_obj.spo2}%"
        if vitals_obj.weight:
            vitals_dict["Weight"] = f"{vitals_obj.weight} kg"
        if vitals_obj.bmi:
            vitals_dict["BMI"] = f"{vitals_obj.bmi}"

        return vitals_dict

    def _extract_history(self, text: str) -> str:
        """Extract history of present illness."""
        # Look for history section
        history_pattern = r"history[:\s]+([^.]+(?:\.[^.]+){0,3})"
        match = re.search(history_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_associated_symptoms(self, text: str) -> List[str]:
        """Extract associated symptoms."""
        symptoms = []
        symptom_keywords = [
            "fever", "pain", "cough", "breathlessness", "vomiting", "diarrhea",
            "dizziness", "weakness", "headache", "nausea", "sweating", "palpitations"
        ]

        for symptom in symptom_keywords:
            if re.search(r'\b' + symptom + r'\b', text, re.IGNORECASE):
                symptoms.append(symptom)

        return symptoms

    def _extract_duration(self, text: str) -> Optional[str]:
        """Extract symptom duration."""
        match = re.search(self.DURATION_PATTERN, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        return None

    def _extract_examination(self, text: str) -> List[str]:
        """Extract examination findings."""
        findings = []

        # Common examination patterns
        exam_patterns = [
            r"on examination[:\s]+([^.]+)",
            r"examination reveals?[:\s]+([^.]+)",
            r"(?:CVS|RS|CNS|Abdomen|chest)[:\s]+([^.]+)",
        ]

        for pattern in exam_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                findings.append(match.group(1).strip())

        return findings

    def _extract_diagnosis_list(self, text: str) -> List[str]:
        """Extract diagnoses."""
        diagnoses = []

        # Look for diagnosis section
        diag_patterns = [
            r"diagnosis[:\s]+([^.]+)",
            r"impression[:\s]+([^.]+)",
            r"assessment[:\s]+([^.]+)",
        ]

        for pattern in diag_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Split by commas or 'and'
                diag_text = match.group(1)
                diagnoses.extend([d.strip() for d in re.split(r',|\band\b', diag_text)])

        return [d for d in diagnoses if d]

    def _extract_investigations(self, text: str) -> List[Investigation]:
        """Extract investigations."""
        investigations = []

        # Common lab tests
        lab_keywords = [
            "CBC", "HbA1c", "creatinine", "urea", "electrolytes", "LFT", "KFT",
            "lipid profile", "TSH", "ECG", "chest X-ray", "ultrasound", "CT scan",
            "MRI", "echo", "TMT", "urine routine"
        ]

        for lab in lab_keywords:
            if re.search(r'\b' + re.escape(lab) + r'\b', text, re.IGNORECASE):
                investigations.append(Investigation(
                    name=lab,
                    test_type="lab" if lab.upper() == lab or "test" in lab.lower() else "imaging"
                ))

        return investigations

    def _extract_advice(self, text: str) -> List[str]:
        """Extract advice/lifestyle recommendations."""
        advice = []

        advice_keywords = [
            r"diet\s+(?:control|modification|restriction)",
            r"exercise\s+regularly?",
            r"avoid\s+\w+",
            r"reduce\s+\w+",
            r"increase\s+\w+",
            r"quit\s+smoking",
            r"limit\s+alcohol",
        ]

        for pattern in advice_keywords:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                advice.append(match.group(0))

        return advice

    def _extract_follow_up(self, text: str) -> Optional[str]:
        """Extract follow-up instructions."""
        followup_pattern = r"follow[\s-]up\s+(?:in|after)\s+(\d+\s+(?:day|week|month)s?)"
        match = re.search(followup_pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    def _enhance_with_llm(self, soap: SOAPNote, transcript: str) -> SOAPNote:
        """Use LLM to enhance SOAP note extraction."""
        # TODO: Implement LLM-based enhancement
        # This would call llm_service.generate() with a specialized prompt
        return soap

    def _extract_medications_with_llm(self, transcript: str) -> List[Medication]:
        """Use LLM to extract medications when pattern matching fails."""
        if not self.llm_service or not self.llm_service.is_available():
            return []

        prompt = f"""Extract medications from this clinical note. Return ONLY valid JSON array.

Clinical Note:
{transcript}

Expected format:
[
  {{
    "drug_name": "Metformin",
    "strength": "500mg",
    "frequency": "BD",
    "duration": "30 days",
    "instructions": "after meals"
  }}
]

JSON:"""

        success, response = self.llm_service.generate(prompt, json_mode=True)
        if success:
            try:
                data = json.loads(response)
                return [Medication(**med) for med in data]
            except:
                pass

        return []
