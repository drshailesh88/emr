"""Adverse event and incident documentation system.

This module handles:
- Near-miss documentation
- Adverse event reporting
- Root cause analysis
- Corrective action tracking
- Regulatory compliance reporting
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Optional
from enum import Enum


class IncidentSeverity(Enum):
    """Severity classification of incidents."""
    NEAR_MISS = "near_miss"  # Caught before reaching patient
    MINOR = "minor"  # Minimal harm, temporary
    MODERATE = "moderate"  # Required intervention
    SEVERE = "severe"  # Permanent harm
    SENTINEL = "sentinel"  # Death or serious permanent harm


class IncidentCategory(Enum):
    """Categories of clinical incidents."""
    MEDICATION_ERROR = "medication_error"
    WRONG_PATIENT = "wrong_patient"
    WRONG_PROCEDURE = "wrong_procedure"
    DELAYED_DIAGNOSIS = "delayed_diagnosis"
    MISSED_DIAGNOSIS = "missed_diagnosis"
    LABORATORY_ERROR = "laboratory_error"
    EQUIPMENT_FAILURE = "equipment_failure"
    COMMUNICATION_FAILURE = "communication_failure"
    DOCUMENTATION_ERROR = "documentation_error"
    FALL = "fall"
    INFECTION = "infection"
    ALLERGIC_REACTION = "allergic_reaction"
    ADVERSE_DRUG_REACTION = "adverse_drug_reaction"
    PROCEDURE_COMPLICATION = "procedure_complication"
    CONSENT_ISSUE = "consent_issue"
    PRIVACY_BREACH = "privacy_breach"
    OTHER = "other"


class IncidentStatus(Enum):
    """Status of incident investigation."""
    REPORTED = "reported"
    UNDER_INVESTIGATION = "under_investigation"
    ROOT_CAUSE_IDENTIFIED = "root_cause_identified"
    CORRECTIVE_ACTION_PLANNED = "corrective_action_planned"
    CORRECTIVE_ACTION_IMPLEMENTED = "corrective_action_implemented"
    CLOSED = "closed"


@dataclass
class CorrectiveAction:
    """A corrective action for an incident."""
    action_id: str
    description: str
    responsible_person: str
    due_date: date
    completed_date: Optional[date]
    status: str  # planned, in_progress, completed
    effectiveness_review: Optional[str]


@dataclass
class IncidentReport:
    """Complete incident report."""
    report_id: str

    # When and where
    incident_date: datetime
    incident_location: str
    reported_date: datetime
    reported_by_id: str
    reported_by_name: str

    # What happened
    category: IncidentCategory
    severity: IncidentSeverity
    title: str
    description: str

    # Who was involved
    patient_id: Optional[int]
    patient_name: Optional[str]
    staff_involved: List[str]

    # Clinical details
    contributing_factors: List[str]
    medications_involved: Optional[List[str]]
    procedures_involved: Optional[List[str]]
    equipment_involved: Optional[List[str]]

    # Investigation
    status: IncidentStatus
    root_cause_analysis: Optional[str]
    immediate_actions_taken: List[str]
    corrective_actions: List[CorrectiveAction]

    # Outcome
    patient_outcome: Optional[str]
    patient_notified: bool
    patient_notification_date: Optional[datetime]
    family_notified: bool

    # Regulatory
    reported_to_authorities: bool
    authority_report_date: Optional[date]
    authority_reference: Optional[str]

    # Metadata
    is_confidential: bool = True
    attachments: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None


class IncidentReporter:
    """
    Incident reporting and investigation system.

    Features:
    - Easy incident documentation
    - Severity-based workflows
    - Root cause analysis templates
    - Corrective action tracking
    - Regulatory compliance support
    - Trend analysis for prevention
    """

    # Contributing factor categories
    CONTRIBUTING_FACTORS = {
        "human": [
            "Fatigue",
            "Distraction",
            "Knowledge gap",
            "Communication failure",
            "Inadequate supervision",
            "Policy violation",
            "Documentation error",
        ],
        "system": [
            "Inadequate staffing",
            "Equipment unavailable",
            "System downtime",
            "Process failure",
            "Unclear protocol",
            "Training gap",
        ],
        "patient": [
            "Communication barrier",
            "Non-compliance",
            "Unreported allergy",
            "Complex condition",
            "Unreported medication",
        ],
        "environmental": [
            "Lighting",
            "Noise",
            "Workspace design",
            "Emergency situation",
        ],
    }

    def __init__(self, db_service, audit_logger=None):
        """Initialize incident reporter."""
        self.db = db_service
        self.audit = audit_logger

    def create_incident_report(
        self,
        reporter_id: str,
        reporter_name: str,
        incident_date: datetime,
        incident_location: str,
        category: IncidentCategory,
        severity: IncidentSeverity,
        title: str,
        description: str,
        patient_id: Optional[int] = None,
        patient_name: Optional[str] = None,
        staff_involved: Optional[List[str]] = None,
        contributing_factors: Optional[List[str]] = None,
        immediate_actions: Optional[List[str]] = None,
        medications_involved: Optional[List[str]] = None,
        procedures_involved: Optional[List[str]] = None,
    ) -> IncidentReport:
        """
        Create a new incident report.

        Args:
            reporter_id: ID of person reporting
            reporter_name: Name of reporter
            incident_date: When incident occurred
            incident_location: Where incident occurred
            category: Category of incident
            severity: Severity level
            title: Brief title
            description: Detailed description
            patient_id: Affected patient (if applicable)
            patient_name: Patient name
            staff_involved: Staff names involved
            contributing_factors: Identified factors
            immediate_actions: Actions already taken
            medications_involved: Any medications involved
            procedures_involved: Any procedures involved

        Returns:
            Created IncidentReport
        """
        report = IncidentReport(
            report_id=str(uuid.uuid4()),
            incident_date=incident_date,
            incident_location=incident_location,
            reported_date=datetime.now(),
            reported_by_id=reporter_id,
            reported_by_name=reporter_name,
            category=category,
            severity=severity,
            title=title,
            description=description,
            patient_id=patient_id,
            patient_name=patient_name,
            staff_involved=staff_involved or [],
            contributing_factors=contributing_factors or [],
            medications_involved=medications_involved,
            procedures_involved=procedures_involved,
            equipment_involved=None,
            status=IncidentStatus.REPORTED,
            root_cause_analysis=None,
            immediate_actions_taken=immediate_actions or [],
            corrective_actions=[],
            patient_outcome=None,
            patient_notified=False,
            patient_notification_date=None,
            family_notified=False,
            reported_to_authorities=False,
            authority_report_date=None,
            authority_reference=None,
        )

        if self.db:
            self.db.store_incident_report(report)

        # Log to audit trail
        if self.audit:
            self.audit.log(
                action=self.audit.AuditAction.INCIDENT_REPORT,
                user_id=reporter_id,
                user_name=reporter_name,
                patient_id=patient_id,
                patient_name=patient_name,
                description=f"Incident reported: {title}",
                resource_type="incident",
                resource_id=report.report_id,
                details={
                    "category": category.value,
                    "severity": severity.value,
                    "location": incident_location,
                },
            )

        # Trigger alerts for severe incidents
        if severity in [IncidentSeverity.SEVERE, IncidentSeverity.SENTINEL]:
            self._trigger_urgent_alert(report)

        return report

    def update_investigation(
        self,
        report_id: str,
        investigator_id: str,
        investigator_name: str,
        root_cause_analysis: Optional[str] = None,
        additional_factors: Optional[List[str]] = None,
        patient_outcome: Optional[str] = None,
    ) -> IncidentReport:
        """Update incident with investigation findings."""
        report = self._get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        if root_cause_analysis:
            report.root_cause_analysis = root_cause_analysis
            report.status = IncidentStatus.ROOT_CAUSE_IDENTIFIED

        if additional_factors:
            report.contributing_factors.extend(additional_factors)

        if patient_outcome:
            report.patient_outcome = patient_outcome

        report.updated_at = datetime.now()

        if self.db:
            self.db.update_incident_report(report)

        # Log update
        if self.audit:
            self.audit.log(
                action=self.audit.AuditAction.INCIDENT_UPDATE,
                user_id=investigator_id,
                user_name=investigator_name,
                patient_id=report.patient_id,
                patient_name=report.patient_name,
                description=f"Investigation updated: {report.title}",
                resource_type="incident",
                resource_id=report_id,
            )

        return report

    def add_corrective_action(
        self,
        report_id: str,
        description: str,
        responsible_person: str,
        due_date: date,
    ) -> CorrectiveAction:
        """Add a corrective action to an incident."""
        report = self._get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        action = CorrectiveAction(
            action_id=str(uuid.uuid4()),
            description=description,
            responsible_person=responsible_person,
            due_date=due_date,
            completed_date=None,
            status="planned",
            effectiveness_review=None,
        )

        report.corrective_actions.append(action)
        report.status = IncidentStatus.CORRECTIVE_ACTION_PLANNED
        report.updated_at = datetime.now()

        if self.db:
            self.db.update_incident_report(report)

        return action

    def complete_corrective_action(
        self,
        report_id: str,
        action_id: str,
        effectiveness_review: Optional[str] = None,
    ) -> IncidentReport:
        """Mark a corrective action as completed."""
        report = self._get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        for action in report.corrective_actions:
            if action.action_id == action_id:
                action.status = "completed"
                action.completed_date = date.today()
                action.effectiveness_review = effectiveness_review
                break

        # Check if all actions are completed
        all_completed = all(
            a.status == "completed" for a in report.corrective_actions
        )
        if all_completed and report.corrective_actions:
            report.status = IncidentStatus.CORRECTIVE_ACTION_IMPLEMENTED

        report.updated_at = datetime.now()

        if self.db:
            self.db.update_incident_report(report)

        return report

    def close_incident(
        self,
        report_id: str,
        closer_id: str,
        closer_name: str,
        closing_summary: str,
    ) -> IncidentReport:
        """Close an incident after all actions are complete."""
        report = self._get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # Verify all corrective actions are completed
        pending_actions = [
            a for a in report.corrective_actions if a.status != "completed"
        ]
        if pending_actions:
            raise ValueError(
                f"Cannot close: {len(pending_actions)} corrective actions pending"
            )

        report.status = IncidentStatus.CLOSED
        report.closed_at = datetime.now()
        report.updated_at = datetime.now()

        if self.db:
            self.db.update_incident_report(report)

        # Log closure
        if self.audit:
            self.audit.log(
                action=self.audit.AuditAction.INCIDENT_CLOSE,
                user_id=closer_id,
                user_name=closer_name,
                patient_id=report.patient_id,
                patient_name=report.patient_name,
                description=f"Incident closed: {report.title}",
                resource_type="incident",
                resource_id=report_id,
                details={"closing_summary": closing_summary},
            )

        return report

    def record_patient_notification(
        self,
        report_id: str,
        notification_date: datetime,
        notification_method: str,
        family_notified: bool = False,
    ) -> IncidentReport:
        """Record that patient was notified of incident."""
        report = self._get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        report.patient_notified = True
        report.patient_notification_date = notification_date
        report.family_notified = family_notified
        report.updated_at = datetime.now()

        if self.db:
            self.db.update_incident_report(report)

        return report

    def record_regulatory_report(
        self,
        report_id: str,
        authority_name: str,
        report_date: date,
        reference_number: str,
    ) -> IncidentReport:
        """Record that incident was reported to authorities."""
        report = self._get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        report.reported_to_authorities = True
        report.authority_report_date = report_date
        report.authority_reference = f"{authority_name}: {reference_number}"
        report.updated_at = datetime.now()

        if self.db:
            self.db.update_incident_report(report)

        return report

    def get_open_incidents(self) -> List[IncidentReport]:
        """Get all non-closed incidents."""
        if self.db:
            return self.db.get_incidents_by_status_not(IncidentStatus.CLOSED)
        return []

    def get_incidents_by_severity(
        self,
        severity: IncidentSeverity
    ) -> List[IncidentReport]:
        """Get incidents by severity level."""
        if self.db:
            return self.db.get_incidents_by_severity(severity)
        return []

    def get_patient_incidents(self, patient_id: int) -> List[IncidentReport]:
        """Get all incidents involving a patient."""
        if self.db:
            return self.db.get_incidents_for_patient(patient_id)
        return []

    def get_incident_trends(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Analyze incident trends for quality improvement.

        Returns:
            Trend analysis with categories, severities, contributing factors
        """
        if not self.db:
            return {}

        incidents = self.db.get_incidents_by_date_range(start_date, end_date)

        # Count by category
        by_category = {}
        for incident in incidents:
            cat = incident.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        # Count by severity
        by_severity = {}
        for incident in incidents:
            sev = incident.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

        # Count contributing factors
        factor_counts = {}
        for incident in incidents:
            for factor in incident.contributing_factors:
                factor_counts[factor] = factor_counts.get(factor, 0) + 1

        # Top contributing factors
        top_factors = sorted(
            factor_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Location analysis
        by_location = {}
        for incident in incidents:
            loc = incident.incident_location
            by_location[loc] = by_location.get(loc, 0) + 1

        # Time analysis (day of week, hour)
        by_day = {}
        by_hour = {}
        for incident in incidents:
            day = incident.incident_date.strftime("%A")
            hour = incident.incident_date.hour
            by_day[day] = by_day.get(day, 0) + 1
            by_hour[hour] = by_hour.get(hour, 0) + 1

        return {
            "period": {"start": start_date, "end": end_date},
            "total_incidents": len(incidents),
            "by_category": by_category,
            "by_severity": by_severity,
            "top_contributing_factors": top_factors,
            "by_location": by_location,
            "by_day_of_week": by_day,
            "by_hour": by_hour,
            "high_risk_areas": self._identify_high_risk_areas(incidents),
            "recommendations": self._generate_recommendations(
                by_category, top_factors
            ),
        }

    def generate_quality_report(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """Generate quality improvement report."""
        trends = self.get_incident_trends(start_date, end_date)

        if not self.db:
            return {"trends": trends}

        # Get closed incidents for analysis
        closed = self.db.get_closed_incidents_by_date_range(start_date, end_date)

        # Time to closure analysis
        closure_times = []
        for incident in closed:
            if incident.closed_at:
                days = (incident.closed_at - incident.reported_date).days
                closure_times.append(days)

        avg_closure_time = (
            sum(closure_times) / len(closure_times) if closure_times else 0
        )

        # Corrective action completion rate
        total_actions = 0
        completed_actions = 0
        overdue_actions = 0
        today = date.today()

        for incident in self.get_open_incidents():
            for action in incident.corrective_actions:
                total_actions += 1
                if action.status == "completed":
                    completed_actions += 1
                elif action.due_date < today:
                    overdue_actions += 1

        return {
            "period": {"start": start_date, "end": end_date},
            "incident_trends": trends,
            "closure_metrics": {
                "average_days_to_close": round(avg_closure_time, 1),
                "total_closed": len(closed),
            },
            "corrective_actions": {
                "total": total_actions,
                "completed": completed_actions,
                "completion_rate": (
                    round(completed_actions / total_actions * 100, 1)
                    if total_actions > 0 else 100
                ),
                "overdue": overdue_actions,
            },
            "sentinel_events": len([
                i for i in trends.get("by_severity", {})
                if i == "sentinel"
            ]),
        }

    def _get_report(self, report_id: str) -> Optional[IncidentReport]:
        """Get incident report by ID."""
        if self.db:
            return self.db.get_incident_by_id(report_id)
        return None

    def _trigger_urgent_alert(self, report: IncidentReport):
        """Trigger urgent alert for severe incidents."""
        # In production, this would:
        # - Send SMS to clinic administrator
        # - Send email to quality committee
        # - Create high-priority task
        pass

    def _identify_high_risk_areas(
        self,
        incidents: List[IncidentReport]
    ) -> List[Dict]:
        """Identify high-risk areas from incidents."""
        # Count incidents by location
        location_severity = {}
        for incident in incidents:
            loc = incident.incident_location
            if loc not in location_severity:
                location_severity[loc] = {"count": 0, "severity_score": 0}

            location_severity[loc]["count"] += 1

            # Weight by severity
            severity_weights = {
                "near_miss": 1,
                "minor": 2,
                "moderate": 3,
                "severe": 5,
                "sentinel": 10,
            }
            location_severity[loc]["severity_score"] += severity_weights.get(
                incident.severity.value, 1
            )

        # Rank by weighted score
        high_risk = sorted(
            location_severity.items(),
            key=lambda x: x[1]["severity_score"],
            reverse=True
        )[:5]

        return [
            {
                "location": loc,
                "incident_count": data["count"],
                "risk_score": data["severity_score"],
            }
            for loc, data in high_risk
        ]

    def _generate_recommendations(
        self,
        by_category: Dict[str, int],
        top_factors: List
    ) -> List[str]:
        """Generate recommendations based on trends."""
        recommendations = []

        # Category-specific recommendations
        if by_category.get("medication_error", 0) > 3:
            recommendations.append(
                "High medication errors: Implement barcode medication "
                "administration and double-check protocols"
            )

        if by_category.get("communication_failure", 0) > 2:
            recommendations.append(
                "Communication failures noted: Consider implementing "
                "structured handoff protocols (SBAR)"
            )

        if by_category.get("documentation_error", 0) > 2:
            recommendations.append(
                "Documentation errors: Review EMR workflows and "
                "provide additional training"
            )

        # Factor-specific recommendations
        factor_recommendations = {
            "Fatigue": "Review staffing levels and shift schedules",
            "Knowledge gap": "Implement targeted training programs",
            "Inadequate staffing": "Review staffing ratios and coverage",
            "Communication failure": "Implement structured communication tools",
            "Equipment unavailable": "Review equipment maintenance and inventory",
        }

        for factor, count in top_factors[:3]:
            if factor in factor_recommendations:
                recommendations.append(
                    f"{factor} identified {count} times: "
                    f"{factor_recommendations[factor]}"
                )

        return recommendations
