"""SQL-based context builder for RAG-like functionality without vector embeddings.

This module provides context retrieval using structured SQL queries instead of
vector embeddings. It's more accurate for structured clinical data and uses
zero additional memory.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import date, timedelta

from ..models.schemas import PatientSnapshot


class QueryParser:
    """Parse natural language queries into structured filters."""

    SPECIALTY_MAP = {
        # Nephrology
        'nephrologist': 'nephrology',
        'nephrology': 'nephrology',
        'kidney': 'nephrology',
        'renal': 'nephrology',
        'dialysis': 'nephrology',
        'creatinine': 'nephrology',

        # Cardiology
        'cardiologist': 'cardiology',
        'cardiology': 'cardiology',
        'heart': 'cardiology',
        'cardiac': 'cardiology',
        'ecg': 'cardiology',
        'echo': 'cardiology',
        'pci': 'cardiology',
        'cabg': 'cardiology',
        'stent': 'cardiology',

        # Neurology
        'neurologist': 'neurology',
        'neurology': 'neurology',
        'brain': 'neurology',
        'neuro': 'neurology',
        'stroke': 'neurology',
        'seizure': 'neurology',

        # Pulmonology
        'pulmonologist': 'pulmonology',
        'pulmonology': 'pulmonology',
        'lung': 'pulmonology',
        'chest': 'pulmonology',
        'respiratory': 'pulmonology',
        'asthma': 'pulmonology',
        'copd': 'pulmonology',

        # Endocrinology
        'endocrinologist': 'endocrinology',
        'endocrine': 'endocrinology',
        'diabetes': 'endocrinology',
        'thyroid': 'endocrinology',
        'sugar': 'endocrinology',
        'hba1c': 'endocrinology',

        # Gastroenterology
        'gastroenterologist': 'gastroenterology',
        'gastro': 'gastroenterology',
        'gi': 'gastroenterology',
        'liver': 'gastroenterology',
        'hepatology': 'gastroenterology',
        'endoscopy': 'gastroenterology',

        # Surgery
        'surgeon': 'surgery',
        'surgical': 'surgery',
        'operation': 'surgery',

        # Orthopedics
        'orthopedic': 'orthopedics',
        'ortho': 'orthopedics',
        'bone': 'orthopedics',
        'fracture': 'orthopedics',
        'joint': 'orthopedics',

        # Psychiatry
        'psychiatrist': 'psychiatry',
        'psychiatry': 'psychiatry',
        'mental': 'psychiatry',
        'depression': 'psychiatry',
        'anxiety': 'psychiatry',
    }

    # Medical term categories for context routing
    LAB_TERMS = {
        'creatinine', 'hba1c', 'hemoglobin', 'sugar', 'lipid', 'cholesterol',
        'thyroid', 'liver', 'kidney', 'cbc', 'urine', 'blood', 'test', 'lab',
        'result', 'report', 'potassium', 'sodium', 'urea', 'bilirubin',
        'albumin', 'protein', 'troponin', 'bnp', 'inr', 'pt', 'aptt'
    }

    MED_TERMS = {
        'medication', 'medicine', 'drug', 'tablet', 'dose', 'prescription',
        'taking', 'started', 'stopped', 'rx', 'treatment', 'therapy'
    }

    PROCEDURE_TERMS = {
        'surgery', 'procedure', 'pci', 'cabg', 'angiography', 'angioplasty',
        'endoscopy', 'biopsy', 'operation', 'catheterization', 'stent'
    }

    HISTORY_TERMS = {
        'history', 'previous', 'past', 'when', 'last', 'first', 'initial',
        'diagnosis', 'diagnosed', 'condition', 'problem'
    }

    TREND_TERMS = {
        'trend', 'over time', 'change', 'progress', 'improving', 'worsening',
        'compare', 'comparison', 'graph', 'chart'
    }

    def parse(self, query: str, patient_id: int = None) -> Dict[str, Any]:
        """
        Parse a natural language query into structured filters.

        Args:
            query: The natural language question
            patient_id: Current patient ID (optional)

        Returns:
            Dictionary with parsed query components
        """
        query_lower = query.lower()
        tokens = set(query_lower.split())

        result = {
            'patient_id': patient_id,
            'specialty': None,
            'doctor_name': None,
            'time_filter': None,
            'query_type': 'general',
            'categories': [],  # What types of data to retrieve
            'keywords': [],
            'test_name': None,
        }

        # Detect specialty
        for term, specialty in self.SPECIALTY_MAP.items():
            if term in query_lower:
                result['specialty'] = specialty
                result['query_type'] = 'consultation_lookup'
                break

        # Detect doctor name pattern
        doctor_patterns = [
            r'dr\.?\s+(\w+)',
            r'doctor\s+(\w+)',
        ]
        for pattern in doctor_patterns:
            match = re.search(pattern, query_lower)
            if match:
                result['doctor_name'] = match.group(1).title()
                result['query_type'] = 'doctor_lookup'
                break

        # Detect time filter
        if any(word in query_lower for word in ['last', 'recent', 'latest', 'current']):
            result['time_filter'] = 'recent'
        elif any(word in query_lower for word in ['first', 'initial', 'earliest']):
            result['time_filter'] = 'first'
        elif 'all' in query_lower or 'history' in query_lower:
            result['time_filter'] = 'all'

        # Detect categories
        if tokens & self.LAB_TERMS:
            result['categories'].append('lab')
            # Try to extract specific test name
            for term in tokens:
                if term in {'creatinine', 'hba1c', 'hemoglobin', 'potassium', 'sodium',
                           'cholesterol', 'triglycerides', 'bilirubin', 'albumin'}:
                    result['test_name'] = term
                    break

        if tokens & self.MED_TERMS:
            result['categories'].append('medication')

        if tokens & self.PROCEDURE_TERMS:
            result['categories'].append('procedure')

        if tokens & self.HISTORY_TERMS:
            result['categories'].append('history')

        if tokens & self.TREND_TERMS:
            result['categories'].append('trend')
            result['query_type'] = 'trend_analysis'

        # Default to general if no categories detected
        if not result['categories']:
            result['categories'] = ['general']

        # Extract keywords (non-stopwords)
        stopwords = {'what', 'is', 'was', 'the', 'a', 'an', 'of', 'for', 'in', 'on',
                     'to', 'with', 'his', 'her', 'their', 'my', 'this', 'that', 'did',
                     'does', 'do', 'how', 'when', 'where', 'why', 'who', 'patient'}
        result['keywords'] = [t for t in tokens if t not in stopwords and len(t) > 2]

        return result


class ContextBuilder:
    """
    Build RAG-like context from SQL queries instead of vector embeddings.

    This approach is more accurate for structured clinical data and uses
    zero additional memory.
    """

    def __init__(self, db_service):
        """
        Initialize context builder.

        Args:
            db_service: The DatabaseService instance
        """
        self.db = db_service
        self.parser = QueryParser()

    def build_context(self, patient_id: int, question: str) -> str:
        """
        Build context for answering a question about a patient.

        Args:
            patient_id: The patient ID
            question: The natural language question

        Returns:
            Formatted context string for LLM
        """
        parsed = self.parser.parse(question, patient_id)

        context_parts = []

        # Always start with patient snapshot header
        snapshot = self.db.get_patient_snapshot(patient_id)
        if snapshot:
            context_parts.append(self._format_snapshot_header(snapshot))
        else:
            # Generate snapshot if not exists
            try:
                snapshot = self.db.compute_patient_snapshot(patient_id)
                context_parts.append(self._format_snapshot_header(snapshot))
            except Exception:
                patient = self.db.get_patient(patient_id)
                if patient:
                    context_parts.append(f"Patient: {patient.name}, {patient.age}{patient.gender}")

        # Route to appropriate context builders based on parsed query
        if parsed['query_type'] == 'consultation_lookup' and parsed['specialty']:
            context_parts.append(self._get_consultation_context(patient_id, parsed['specialty']))

        elif parsed['query_type'] == 'doctor_lookup' and parsed['doctor_name']:
            context_parts.append(self._get_doctor_context(patient_id, parsed['doctor_name']))

        elif parsed['query_type'] == 'trend_analysis' and parsed['test_name']:
            context_parts.append(self._get_trend_context(patient_id, parsed['test_name']))

        else:
            # General context building based on categories
            for category in parsed['categories']:
                if category == 'lab':
                    if parsed['test_name']:
                        context_parts.append(self._get_specific_lab_context(
                            patient_id, parsed['test_name'], parsed['time_filter']
                        ))
                    else:
                        context_parts.append(self._get_lab_context(patient_id, parsed['time_filter']))

                elif category == 'medication':
                    context_parts.append(self._get_medication_context(patient_id))

                elif category == 'procedure':
                    context_parts.append(self._get_procedure_context(patient_id))

                elif category == 'history':
                    context_parts.append(self._get_visit_history_context(patient_id, parsed['time_filter']))

                elif category == 'general':
                    # Include a bit of everything
                    context_parts.append(self._get_recent_summary_context(patient_id))

        # Use FTS for keyword search if we have keywords and context is thin
        if parsed['keywords'] and len(''.join(context_parts)) < 500:
            fts_context = self._get_fts_context(patient_id, ' '.join(parsed['keywords']))
            if fts_context:
                context_parts.append(fts_context)

        return "\n\n".join(filter(None, context_parts))

    def _format_snapshot_header(self, snapshot: PatientSnapshot) -> str:
        """Format patient snapshot as context header."""
        lines = [
            "═" * 50,
            f"PATIENT: {snapshot.demographics} | UHID: {snapshot.uhid}",
            "═" * 50,
        ]

        if snapshot.allergies:
            lines.append(f"⚠️ ALLERGIES: {', '.join(snapshot.allergies)}")
        else:
            lines.append("✓ No Known Drug Allergies")

        if snapshot.active_problems:
            lines.append(f"Active Problems: {', '.join(snapshot.active_problems[:5])}")

        if snapshot.on_anticoagulation:
            lines.append(f"💉 On Anticoagulation: {snapshot.anticoag_drug}")

        return "\n".join(lines)

    def _get_consultation_context(self, patient_id: int, specialty: str) -> str:
        """Get consultation context for a specialty."""
        consults = self.db.get_consultations_by_specialty(patient_id, specialty, limit=5)

        if not consults:
            return f"No {specialty} consultations found for this patient."

        lines = [f"=== {specialty.upper()} CONSULTATIONS ==="]

        for c in consults:
            lines.append(f"\n📋 {c.get('consult_date', 'Unknown date')}")
            if c.get('doctor_name'):
                lines.append(f"   Doctor: Dr. {c['doctor_name']} ({c.get('designation', '')})")
            if c.get('reason_for_referral'):
                lines.append(f"   Reason: {c['reason_for_referral']}")
            if c.get('findings'):
                lines.append(f"   Findings: {c['findings']}")
            if c.get('impression'):
                lines.append(f"   Impression: {c['impression']}")
            if c.get('recommendations'):
                lines.append(f"   Recommendations: {c['recommendations']}")

        return "\n".join(lines)

    def _get_doctor_context(self, patient_id: int, doctor_name: str) -> str:
        """Get context for a specific doctor's notes."""
        # Search visits and consultations by doctor name
        all_consults = self.db.get_all_patient_consultations(patient_id, limit=20)

        matching = [c for c in all_consults
                    if c.get('doctor_name', '').lower().find(doctor_name.lower()) >= 0]

        if not matching:
            return f"No records found from Dr. {doctor_name}"

        lines = [f"=== RECORDS FROM DR. {doctor_name.upper()} ==="]

        for c in matching:
            lines.append(f"\n📋 {c.get('consult_date', 'Unknown date')} - {c.get('specialty', 'Unknown specialty')}")
            if c.get('findings'):
                lines.append(f"   Findings: {c['findings']}")
            if c.get('recommendations'):
                lines.append(f"   Recommendations: {c['recommendations']}")

        return "\n".join(lines)

    def _get_lab_context(self, patient_id: int, time_filter: str = None) -> str:
        """Get lab results context."""
        investigations = self.db.get_patient_investigations(patient_id)

        if not investigations:
            return "No laboratory investigations on record."

        # Apply time filter
        if time_filter == 'recent':
            investigations = investigations[:10]
        elif time_filter == 'first':
            investigations = investigations[-5:]

        lines = ["=== INVESTIGATIONS ==="]

        for inv in investigations[:15]:
            abnormal = " ⚠️ ABNORMAL" if inv.is_abnormal else ""
            lines.append(f"• {inv.test_date}: {inv.test_name} = {inv.result} {inv.unit}{abnormal}")

        return "\n".join(lines)

    def _get_specific_lab_context(self, patient_id: int, test_name: str, time_filter: str = None) -> str:
        """Get context for a specific lab test."""
        investigations = self.db.get_patient_investigations(patient_id)

        matching = [inv for inv in investigations
                    if test_name.lower() in inv.test_name.lower()]

        if not matching:
            return f"No {test_name} results found."

        lines = [f"=== {test_name.upper()} RESULTS ==="]

        for inv in matching[:10]:
            abnormal = " ⚠️ ABNORMAL" if inv.is_abnormal else ""
            lines.append(f"• {inv.test_date}: {inv.result} {inv.unit}{abnormal}")

        # Add trend analysis if multiple results
        if len(matching) > 1:
            try:
                first_val = float(re.search(r'[\d.]+', matching[-1].result).group())
                last_val = float(re.search(r'[\d.]+', matching[0].result).group())
                change = ((last_val - first_val) / first_val) * 100 if first_val != 0 else 0

                if change > 10:
                    lines.append(f"\n📈 Trend: Increased by {abs(change):.1f}% over time")
                elif change < -10:
                    lines.append(f"\n📉 Trend: Decreased by {abs(change):.1f}% over time")
                else:
                    lines.append(f"\n➡️ Trend: Stable")
            except (ValueError, AttributeError):
                pass

        return "\n".join(lines)

    def _get_trend_context(self, patient_id: int, test_name: str) -> str:
        """Get trend analysis context for a specific test."""
        return self._get_specific_lab_context(patient_id, test_name, 'all')

    def _get_medication_context(self, patient_id: int) -> str:
        """Get medication context."""
        snapshot = self.db.get_patient_snapshot(patient_id)

        if snapshot and snapshot.current_medications:
            lines = ["=== CURRENT MEDICATIONS ==="]
            for med in snapshot.current_medications:
                lines.append(f"• {med.drug_name} {med.strength} - {med.dose} {med.frequency}")
                if med.instructions:
                    lines.append(f"  ({med.instructions})")
            return "\n".join(lines)

        # Fall back to most recent prescription
        visits = self.db.get_patient_visits(patient_id)
        for visit in visits:
            if visit.prescription_json:
                try:
                    import json
                    rx = json.loads(visit.prescription_json)
                    if rx.get('medications'):
                        lines = [f"=== MEDICATIONS (as of {visit.visit_date}) ==="]
                        for med in rx['medications']:
                            lines.append(f"• {med.get('drug_name', 'Unknown')} {med.get('strength', '')} - {med.get('dose', '')} {med.get('frequency', '')}")
                        return "\n".join(lines)
                except Exception:
                    pass

        return "No medication records found."

    def _get_procedure_context(self, patient_id: int) -> str:
        """Get procedure context."""
        procedures = self.db.get_patient_procedures(patient_id)

        if not procedures:
            return "No procedures on record."

        lines = ["=== PROCEDURES ==="]

        for proc in procedures[:10]:
            lines.append(f"\n🔧 {proc.procedure_date}: {proc.procedure_name}")
            if proc.details:
                lines.append(f"   Details: {proc.details}")
            if proc.notes:
                lines.append(f"   Notes: {proc.notes}")

        return "\n".join(lines)

    def _get_visit_history_context(self, patient_id: int, time_filter: str = None) -> str:
        """Get visit history context."""
        visits = self.db.get_patient_visits(patient_id)

        if not visits:
            return "No visit records found."

        # Apply time filter
        if time_filter == 'recent':
            visits = visits[:5]
        elif time_filter == 'first':
            visits = visits[-3:]
        else:
            visits = visits[:10]

        lines = ["=== VISIT HISTORY ==="]

        for visit in visits:
            lines.append(f"\n📅 {visit.visit_date}")
            if visit.chief_complaint:
                lines.append(f"   Chief Complaint: {visit.chief_complaint}")
            if visit.diagnosis:
                lines.append(f"   Diagnosis: {visit.diagnosis}")
            if visit.clinical_notes:
                # Truncate long notes
                notes = visit.clinical_notes[:200]
                if len(visit.clinical_notes) > 200:
                    notes += "..."
                lines.append(f"   Notes: {notes}")

        return "\n".join(lines)

    def _get_recent_summary_context(self, patient_id: int) -> str:
        """Get a summary of recent activity."""
        context_parts = []

        # Recent visits
        visits = self.db.get_patient_visits(patient_id)
        if visits:
            lines = ["=== RECENT VISITS ==="]
            for visit in visits[:3]:
                lines.append(f"• {visit.visit_date}: {visit.chief_complaint or 'No complaint recorded'}")
                if visit.diagnosis:
                    lines.append(f"  Diagnosis: {visit.diagnosis}")
            context_parts.append("\n".join(lines))

        # Key labs
        snapshot = self.db.get_patient_snapshot(patient_id)
        if snapshot and snapshot.key_labs:
            lines = ["=== KEY LAB VALUES ==="]
            for test, data in snapshot.key_labs.items():
                abnormal = " ⚠️" if data.get('abnormal') else ""
                lines.append(f"• {test}: {data.get('value', 'N/A')} {data.get('unit', '')} ({data.get('date', 'Unknown')}){abnormal}")
            context_parts.append("\n".join(lines))

        # Recent procedures
        procedures = self.db.get_patient_procedures(patient_id)
        if procedures:
            lines = ["=== PROCEDURES ==="]
            for proc in procedures[:3]:
                lines.append(f"• {proc.procedure_date}: {proc.procedure_name}")
            context_parts.append("\n".join(lines))

        return "\n\n".join(context_parts) if context_parts else "No recent activity on record."

    def _get_fts_context(self, patient_id: int, keywords: str) -> str:
        """Use FTS5 to find relevant content by keywords."""
        try:
            results = self.db.fts_search_clinical(keywords, patient_id=patient_id, limit=5)

            if not results:
                return ""

            lines = ["=== RELATED RECORDS ==="]
            for result in results:
                doc_type = result.get('doc_type', 'record')
                doc_date = result.get('doc_date', 'Unknown date')
                content = result.get('content', '')[:200]
                lines.append(f"[{doc_type.upper()} - {doc_date}] {content}")

            return "\n".join(lines)
        except Exception:
            return ""
