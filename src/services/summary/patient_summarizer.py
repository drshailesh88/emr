"""AI-powered patient summary generation"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import date, datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatientSummary:
    """The 30-second patient brief"""
    # The 30-second brief
    one_liner: str                      # Single sentence capturing patient essence
    key_diagnoses: List[str]            # Major diagnoses with duration
    current_medications: List[str]      # Active medications (drug + dose)
    recent_trends: List[str]            # What's improving/worsening
    red_flags: List[str]                # Concerns requiring attention
    care_gaps: List[str]                # Overdue preventive care
    last_visit_summary: str             # What happened last time
    risk_level: str                     # low, moderate, high
    generated_at: datetime = field(default_factory=datetime.now)


class PatientSummarizer:
    """Generate intelligent patient summaries using LLM"""

    SUMMARY_PROMPT = '''You are a medical AI assistant. Generate a concise clinical summary for a doctor who is about to see this patient. Focus on what's ACTIONABLE and IMPORTANT.

PATIENT DATA:
Name: {name}
Age: {age} | Gender: {gender}
UHID: {uhid}

DIAGNOSES (with dates diagnosed):
{diagnoses}

CURRENT MEDICATIONS:
{medications}

ALLERGIES:
{allergies}

RECENT VISITS (last 6 months):
{visits}

RECENT LAB RESULTS:
{labs}

RECENT VITALS:
{vitals}

Generate a summary in this exact JSON format:
{{
    "one_liner": "Single sentence capturing who this patient is medically",
    "key_diagnoses": ["Diabetes mellitus type 2 (5 years)", "Hypertension (3 years)"],
    "current_medications": ["Metformin 500mg BD", "Amlodipine 5mg OD"],
    "recent_trends": ["HbA1c improving: 8.2% → 7.5%", "BP at target: 130/80"],
    "red_flags": ["Creatinine trending up (1.2 → 1.6) - nephrology referral?"],
    "care_gaps": ["Eye exam overdue by 8 months", "Lipid panel due"],
    "last_visit_summary": "Came for diabetes follow-up. Sugar better controlled. Added ACE inhibitor for proteinuria.",
    "risk_level": "moderate"
}}

Guidelines:
- Be concise but comprehensive
- Focus on what doctor needs to know NOW
- Flag actionable items
- Use common abbreviations (DM, HTN, CAD, etc.)
- Return ONLY valid JSON'''

    VISIT_SUMMARY_PROMPT = '''Summarize this clinical visit in 2-3 sentences. Focus on what happened and what was decided.

VISIT DATA:
Date: {visit_date}
Chief Complaint: {chief_complaint}
Clinical Notes: {clinical_notes}
Diagnosis: {diagnosis}

Return ONLY the summary text, no JSON.'''

    def __init__(self, llm_service, db_service):
        self.llm = llm_service
        self.db = db_service

    def generate_summary(self, patient_id: int) -> PatientSummary:
        """Generate comprehensive patient summary"""
        try:
            # Fetch patient data
            patient = self.db.get_patient(patient_id)
            if not patient:
                raise ValueError(f"Patient {patient_id} not found")

            # Get all relevant data
            visits = self.db.get_patient_visits(patient_id)
            investigations = self.db.get_patient_investigations(patient_id)
            procedures = self.db.get_patient_procedures(patient_id)

            # Format data for prompt
            diagnoses_text = self._format_diagnoses(visits)
            medications_text = self._format_medications(visits)
            visits_text = self._format_visits(visits[:6])  # Last 6 visits
            labs_text = self._format_labs(investigations[:20])  # Last 20 labs
            vitals_text = self._format_vitals(visits)

            # Build prompt
            prompt = self.SUMMARY_PROMPT.format(
                name=patient.name,
                age=patient.age or "Unknown",
                gender=patient.gender or "Unknown",
                uhid=patient.uhid or "Unknown",
                diagnoses=diagnoses_text,
                medications=medications_text,
                allergies="None documented",  # TODO: Add allergies table
                visits=visits_text,
                labs=labs_text,
                vitals=vitals_text,
            )

            # Call LLM
            response = self.llm.query(prompt)

            # Parse JSON response
            try:
                # Extract JSON from response (handle markdown code blocks)
                json_str = response.strip()
                if json_str.startswith("```"):
                    lines = json_str.split("\n")
                    json_str = "\n".join(lines[1:-1])

                data = json.loads(json_str)

                return PatientSummary(
                    one_liner=data.get("one_liner", "No summary available"),
                    key_diagnoses=data.get("key_diagnoses", []),
                    current_medications=data.get("current_medications", []),
                    recent_trends=data.get("recent_trends", []),
                    red_flags=data.get("red_flags", []),
                    care_gaps=data.get("care_gaps", []),
                    last_visit_summary=data.get("last_visit_summary", "No recent visits"),
                    risk_level=data.get("risk_level", "unknown"),
                )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Response was: {response}")

                # Return fallback summary
                return self._generate_fallback_summary(patient, visits, investigations)

        except Exception as e:
            logger.error(f"Error generating patient summary: {e}")
            raise

    def generate_visit_summary(self, visit_id: int) -> str:
        """Summarize a single visit"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM visits WHERE id = ?", (visit_id,))
                row = cursor.fetchone()

                if not row:
                    return "Visit not found"

                visit_dict = dict(row)

                prompt = self.VISIT_SUMMARY_PROMPT.format(
                    visit_date=visit_dict.get("visit_date", "Unknown"),
                    chief_complaint=visit_dict.get("chief_complaint", "Not recorded"),
                    clinical_notes=visit_dict.get("clinical_notes", "Not recorded"),
                    diagnosis=visit_dict.get("diagnosis", "Not recorded"),
                )

                return self.llm.query(prompt)

        except Exception as e:
            logger.error(f"Error generating visit summary: {e}")
            return "Error generating summary"

    def compare_visits(self, current_visit_id: int,
                      previous_visit_id: int) -> Dict:
        """Compare what's changed between visits"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Get both visits
                cursor.execute("SELECT * FROM visits WHERE id IN (?, ?)",
                             (current_visit_id, previous_visit_id))
                rows = cursor.fetchall()

                if len(rows) != 2:
                    return {"error": "One or both visits not found"}

                visits = {dict(row)["id"]: dict(row) for row in rows}
                current = visits[current_visit_id]
                previous = visits[previous_visit_id]

                # Compare diagnoses
                diagnosis_changes = self._compare_field(
                    previous.get("diagnosis", ""),
                    current.get("diagnosis", "")
                )

                # Compare prescriptions
                rx_changes = self._compare_prescriptions(
                    previous.get("prescription_json"),
                    current.get("prescription_json")
                )

                return {
                    "time_between": self._calculate_days_between(
                        previous.get("visit_date"),
                        current.get("visit_date")
                    ),
                    "diagnosis_changes": diagnosis_changes,
                    "prescription_changes": rx_changes,
                    "complaint_changed": previous.get("chief_complaint") != current.get("chief_complaint"),
                }

        except Exception as e:
            logger.error(f"Error comparing visits: {e}")
            return {"error": str(e)}

    def generate_handoff_summary(self, patient_id: int) -> str:
        """Generate handoff summary for referral/transfer"""
        try:
            summary = self.generate_summary(patient_id)
            patient = self.db.get_patient(patient_id)

            handoff = f"""PATIENT HANDOFF SUMMARY

Patient: {patient.name} ({patient.age}{patient.gender})
UHID: {patient.uhid}

ONE-LINE SUMMARY:
{summary.one_liner}

KEY DIAGNOSES:
{self._format_list(summary.key_diagnoses)}

CURRENT MEDICATIONS:
{self._format_list(summary.current_medications)}

RED FLAGS / CONCERNS:
{self._format_list(summary.red_flags) if summary.red_flags else "None"}

RECENT TRENDS:
{self._format_list(summary.recent_trends) if summary.recent_trends else "Stable"}

LAST VISIT:
{summary.last_visit_summary}

CARE GAPS:
{self._format_list(summary.care_gaps) if summary.care_gaps else "None identified"}

RISK LEVEL: {summary.risk_level.upper()}

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
"""
            return handoff

        except Exception as e:
            logger.error(f"Error generating handoff summary: {e}")
            return f"Error generating handoff summary: {e}"

    def _format_diagnoses(self, visits: List) -> str:
        """Format diagnoses for prompt"""
        if not visits:
            return "None documented"

        diagnoses = set()
        for visit in visits[:10]:  # Last 10 visits
            if visit.diagnosis:
                # Split on commas or newlines
                parts = visit.diagnosis.replace("\n", ",").split(",")
                diagnoses.update([d.strip() for d in parts if d.strip()])

        if not diagnoses:
            return "None documented"

        return "\n".join([f"- {d}" for d in sorted(diagnoses)])

    def _format_medications(self, visits: List) -> str:
        """Format medications for prompt"""
        if not visits:
            return "None documented"

        # Get most recent visit with prescription
        for visit in visits:
            if visit.prescription_json:
                try:
                    rx = json.loads(visit.prescription_json)
                    meds = rx.get("medications", [])
                    if meds:
                        return "\n".join([
                            f"- {m.get('drug_name', '')} {m.get('strength', '')} {m.get('frequency', '')}"
                            for m in meds
                        ])
                except json.JSONDecodeError:
                    continue

        return "None documented"

    def _format_visits(self, visits: List) -> str:
        """Format visits for prompt"""
        if not visits:
            return "No recent visits"

        formatted = []
        for visit in visits:
            visit_date = visit.visit_date or "Unknown date"
            complaint = visit.chief_complaint or "No complaint"
            diagnosis = visit.diagnosis or "No diagnosis"

            formatted.append(
                f"{visit_date}: {complaint} → {diagnosis}"
            )

        return "\n".join(formatted)

    def _format_labs(self, investigations: List) -> str:
        """Format lab results for prompt"""
        if not investigations:
            return "No recent lab results"

        formatted = []
        for inv in investigations[:15]:  # Last 15 labs
            test_date = inv.test_date or "Unknown"
            abnormal = " ⚠" if inv.is_abnormal else ""

            formatted.append(
                f"{test_date}: {inv.test_name} = {inv.result} {inv.unit}{abnormal}"
            )

        return "\n".join(formatted)

    def _format_vitals(self, visits: List) -> str:
        """Format vitals from visit notes"""
        # TODO: This is a placeholder. In production, extract vitals from clinical notes
        # or use a separate vitals table
        return "Vitals: See clinical notes"

    def _generate_fallback_summary(self, patient, visits, investigations) -> PatientSummary:
        """Generate a basic summary without LLM"""
        one_liner = f"{patient.name}, {patient.age}{patient.gender}"

        # Extract diagnoses from recent visits
        diagnoses = set()
        for visit in visits[:5]:
            if visit.diagnosis:
                parts = visit.diagnosis.replace("\n", ",").split(",")
                diagnoses.update([d.strip() for d in parts if d.strip()])

        # Get medications from most recent prescription
        medications = []
        for visit in visits:
            if visit.prescription_json:
                try:
                    rx = json.loads(visit.prescription_json)
                    meds = rx.get("medications", [])
                    medications = [
                        f"{m.get('drug_name', '')} {m.get('strength', '')}"
                        for m in meds[:5]
                    ]
                    break
                except:
                    pass

        last_visit = ""
        if visits:
            last_visit = f"Last seen {visits[0].visit_date}: {visits[0].chief_complaint or 'Follow-up'}"

        return PatientSummary(
            one_liner=one_liner,
            key_diagnoses=list(diagnoses)[:5],
            current_medications=medications,
            recent_trends=[],
            red_flags=[],
            care_gaps=[],
            last_visit_summary=last_visit,
            risk_level="unknown",
        )

    def _compare_field(self, old: str, new: str) -> str:
        """Compare two text fields"""
        if old == new:
            return "No change"
        if not old:
            return f"Added: {new}"
        if not new:
            return f"Removed: {old}"
        return f"Changed from '{old}' to '{new}'"

    def _compare_prescriptions(self, old_json: Optional[str], new_json: Optional[str]) -> Dict:
        """Compare two prescriptions"""
        try:
            old_rx = json.loads(old_json) if old_json else {}
            new_rx = json.loads(new_json) if new_json else {}

            old_meds = set([m.get("drug_name", "") for m in old_rx.get("medications", [])])
            new_meds = set([m.get("drug_name", "") for m in new_rx.get("medications", [])])

            return {
                "added": list(new_meds - old_meds),
                "removed": list(old_meds - new_meds),
                "continued": list(old_meds & new_meds),
            }
        except:
            return {"error": "Could not parse prescriptions"}

    def _calculate_days_between(self, date1: Optional[str], date2: Optional[str]) -> int:
        """Calculate days between two dates"""
        try:
            if not date1 or not date2:
                return 0
            d1 = datetime.strptime(str(date1), "%Y-%m-%d")
            d2 = datetime.strptime(str(date2), "%Y-%m-%d")
            return abs((d2 - d1).days)
        except:
            return 0

    def _format_list(self, items: List[str]) -> str:
        """Format list as bullet points"""
        if not items:
            return "None"
        return "\n".join([f"- {item}" for item in items])
