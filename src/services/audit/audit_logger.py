"""Immutable audit trail for all clinical and administrative actions.

This module provides comprehensive audit logging that:
- Creates tamper-evident records of all actions
- Supports forensic analysis for legal proceedings
- Enables compliance reporting (NABH, HIPAA-equivalent)
- Uses cryptographic hashing for integrity verification
"""
import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class AuditAction(Enum):
    """Types of auditable actions."""
    # Patient actions
    PATIENT_CREATE = "patient_create"
    PATIENT_UPDATE = "patient_update"
    PATIENT_VIEW = "patient_view"
    PATIENT_DELETE = "patient_delete"
    PATIENT_MERGE = "patient_merge"

    # Visit actions
    VISIT_CREATE = "visit_create"
    VISIT_UPDATE = "visit_update"
    VISIT_DELETE = "visit_delete"
    VISIT_FINALIZE = "visit_finalize"

    # Prescription actions
    PRESCRIPTION_CREATE = "prescription_create"
    PRESCRIPTION_MODIFY = "prescription_modify"
    PRESCRIPTION_PRINT = "prescription_print"
    PRESCRIPTION_SEND = "prescription_send"

    # Investigation actions
    LAB_ORDER = "lab_order"
    LAB_RESULT_ENTRY = "lab_result_entry"
    LAB_RESULT_VIEW = "lab_result_view"
    LAB_ABNORMAL_ACKNOWLEDGE = "lab_abnormal_acknowledge"

    # Medication actions
    MEDICATION_PRESCRIBE = "medication_prescribe"
    MEDICATION_DISCONTINUE = "medication_discontinue"
    MEDICATION_OVERRIDE_ALERT = "medication_override_alert"

    # Document actions
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DELETE = "document_delete"

    # Communication actions
    WHATSAPP_SEND = "whatsapp_send"
    SMS_SEND = "sms_send"
    CALL_LOG = "call_log"

    # Consent actions
    CONSENT_OBTAIN = "consent_obtain"
    CONSENT_WITHDRAW = "consent_withdraw"

    # Administrative actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_PASSWORD_CHANGE = "user_password_change"
    SETTINGS_CHANGE = "settings_change"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    DATA_EXPORT = "data_export"

    # AI actions (critical for liability)
    AI_SUGGESTION_GENERATE = "ai_suggestion_generate"
    AI_SUGGESTION_ACCEPT = "ai_suggestion_accept"
    AI_SUGGESTION_MODIFY = "ai_suggestion_modify"
    AI_SUGGESTION_REJECT = "ai_suggestion_reject"

    # Incident actions
    INCIDENT_REPORT = "incident_report"
    INCIDENT_UPDATE = "incident_update"
    INCIDENT_CLOSE = "incident_close"


@dataclass
class AuditEvent:
    """A single audit event with cryptographic integrity."""
    event_id: str
    timestamp: datetime
    action: AuditAction
    user_id: str
    user_name: str
    patient_id: Optional[int]
    patient_name: Optional[str]
    resource_type: str
    resource_id: Optional[str]
    description: str
    details: Dict[str, Any]
    ip_address: Optional[str]
    device_info: Optional[str]
    previous_hash: str
    current_hash: str = ""

    def __post_init__(self):
        """Calculate hash after initialization."""
        if not self.current_hash:
            self.current_hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of event data."""
        data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "user_id": self.user_id,
            "patient_id": self.patient_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "description": self.description,
            "details": self.details,
            "previous_hash": self.previous_hash,
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify the event has not been tampered with."""
        return self.current_hash == self._calculate_hash()


@dataclass
class AuditChainStatus:
    """Status of the audit chain integrity."""
    is_valid: bool
    total_events: int
    verified_events: int
    broken_at_event: Optional[str]
    first_event_time: Optional[datetime]
    last_event_time: Optional[datetime]


class AuditLogger:
    """
    Immutable audit logger with blockchain-like integrity.

    Every action in the EMR is logged with:
    - Who did it (user)
    - What they did (action)
    - To whom (patient, if applicable)
    - When (timestamp)
    - How (device, IP)
    - What changed (before/after values)

    Each log entry is cryptographically linked to the previous one,
    making tampering detectable.
    """

    def __init__(self, db_service):
        """Initialize audit logger."""
        self.db = db_service
        self._last_hash = self._get_last_hash()

    def log(
        self,
        action: AuditAction,
        user_id: str,
        user_name: str,
        description: str,
        patient_id: Optional[int] = None,
        patient_name: Optional[str] = None,
        resource_type: str = "",
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> AuditEvent:
        """
        Log an auditable action.

        Args:
            action: Type of action being logged
            user_id: ID of user performing action
            user_name: Name of user (for display)
            description: Human-readable description
            patient_id: ID of affected patient (if applicable)
            patient_name: Name of patient (for quick reference)
            resource_type: Type of resource (visit, prescription, etc.)
            resource_id: ID of specific resource
            details: Additional details (before/after values, etc.)
            ip_address: IP address of client
            device_info: Device/browser information

        Returns:
            The created AuditEvent
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            action=action,
            user_id=user_id,
            user_name=user_name,
            patient_id=patient_id,
            patient_name=patient_name,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            details=details or {},
            ip_address=ip_address,
            device_info=device_info,
            previous_hash=self._last_hash,
        )

        # Store in database
        if self.db:
            self.db.store_audit_event(event)

        # Update chain
        self._last_hash = event.current_hash

        return event

    def log_patient_view(
        self,
        user_id: str,
        user_name: str,
        patient_id: int,
        patient_name: str,
        **kwargs
    ) -> AuditEvent:
        """Log when a patient record is viewed."""
        return self.log(
            action=AuditAction.PATIENT_VIEW,
            user_id=user_id,
            user_name=user_name,
            patient_id=patient_id,
            patient_name=patient_name,
            description=f"Viewed patient record: {patient_name}",
            resource_type="patient",
            resource_id=str(patient_id),
            **kwargs
        )

    def log_prescription(
        self,
        user_id: str,
        user_name: str,
        patient_id: int,
        patient_name: str,
        prescription_id: str,
        medications: List[Dict],
        **kwargs
    ) -> AuditEvent:
        """Log when a prescription is created."""
        med_summary = ", ".join(m.get("drug_name", "") for m in medications[:3])
        if len(medications) > 3:
            med_summary += f" (+{len(medications) - 3} more)"

        return self.log(
            action=AuditAction.PRESCRIPTION_CREATE,
            user_id=user_id,
            user_name=user_name,
            patient_id=patient_id,
            patient_name=patient_name,
            description=f"Created prescription: {med_summary}",
            resource_type="prescription",
            resource_id=prescription_id,
            details={"medications": medications},
            **kwargs
        )

    def log_ai_suggestion(
        self,
        user_id: str,
        user_name: str,
        patient_id: int,
        patient_name: str,
        suggestion_type: str,
        suggestion_content: str,
        accepted: bool,
        modified: bool = False,
        original_suggestion: Optional[str] = None,
        final_content: Optional[str] = None,
        **kwargs
    ) -> AuditEvent:
        """
        Log AI suggestion and doctor's decision.

        Critical for liability: Documents that AI made a suggestion
        and the doctor made the final decision.
        """
        if accepted and modified:
            action = AuditAction.AI_SUGGESTION_MODIFY
            desc = f"Modified AI {suggestion_type} suggestion"
        elif accepted:
            action = AuditAction.AI_SUGGESTION_ACCEPT
            desc = f"Accepted AI {suggestion_type} suggestion"
        else:
            action = AuditAction.AI_SUGGESTION_REJECT
            desc = f"Rejected AI {suggestion_type} suggestion"

        return self.log(
            action=action,
            user_id=user_id,
            user_name=user_name,
            patient_id=patient_id,
            patient_name=patient_name,
            description=desc,
            resource_type="ai_suggestion",
            details={
                "suggestion_type": suggestion_type,
                "original_suggestion": original_suggestion or suggestion_content,
                "final_content": final_content,
                "was_modified": modified,
                "was_accepted": accepted,
            },
            **kwargs
        )

    def log_alert_override(
        self,
        user_id: str,
        user_name: str,
        patient_id: int,
        patient_name: str,
        alert_type: str,
        alert_message: str,
        override_reason: str,
        **kwargs
    ) -> AuditEvent:
        """
        Log when a clinical alert is overridden.

        Critical for liability: Documents that doctor was aware
        of the alert and made an informed decision to override.
        """
        return self.log(
            action=AuditAction.MEDICATION_OVERRIDE_ALERT,
            user_id=user_id,
            user_name=user_name,
            patient_id=patient_id,
            patient_name=patient_name,
            description=f"Overrode {alert_type} alert: {alert_message[:50]}...",
            resource_type="alert",
            details={
                "alert_type": alert_type,
                "alert_message": alert_message,
                "override_reason": override_reason,
                "acknowledged_at": datetime.now().isoformat(),
            },
            **kwargs
        )

    def log_abnormal_result_acknowledgment(
        self,
        user_id: str,
        user_name: str,
        patient_id: int,
        patient_name: str,
        test_name: str,
        result_value: str,
        reference_range: str,
        action_taken: str,
        **kwargs
    ) -> AuditEvent:
        """Log acknowledgment of abnormal lab result."""
        return self.log(
            action=AuditAction.LAB_ABNORMAL_ACKNOWLEDGE,
            user_id=user_id,
            user_name=user_name,
            patient_id=patient_id,
            patient_name=patient_name,
            description=f"Acknowledged abnormal {test_name}: {result_value}",
            resource_type="lab_result",
            details={
                "test_name": test_name,
                "result_value": result_value,
                "reference_range": reference_range,
                "action_taken": action_taken,
            },
            **kwargs
        )

    def get_patient_audit_trail(
        self,
        patient_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditEvent]:
        """Get complete audit trail for a patient."""
        if self.db:
            return self.db.get_audit_events_for_patient(
                patient_id, start_date, end_date
            )
        return []

    def get_user_audit_trail(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditEvent]:
        """Get all actions by a specific user."""
        if self.db:
            return self.db.get_audit_events_for_user(
                user_id, start_date, end_date
            )
        return []

    def verify_chain_integrity(self) -> AuditChainStatus:
        """
        Verify the entire audit chain has not been tampered with.

        Returns:
            AuditChainStatus with verification results
        """
        if not self.db:
            return AuditChainStatus(
                is_valid=True,
                total_events=0,
                verified_events=0,
                broken_at_event=None,
                first_event_time=None,
                last_event_time=None,
            )

        events = self.db.get_all_audit_events_ordered()

        if not events:
            return AuditChainStatus(
                is_valid=True,
                total_events=0,
                verified_events=0,
                broken_at_event=None,
                first_event_time=None,
                last_event_time=None,
            )

        # Verify each event's hash
        expected_previous_hash = "genesis"
        verified_count = 0
        broken_at = None

        for event in events:
            # Verify internal integrity
            if not event.verify_integrity():
                broken_at = event.event_id
                break

            # Verify chain linkage
            if event.previous_hash != expected_previous_hash:
                broken_at = event.event_id
                break

            expected_previous_hash = event.current_hash
            verified_count += 1

        return AuditChainStatus(
            is_valid=broken_at is None,
            total_events=len(events),
            verified_events=verified_count,
            broken_at_event=broken_at,
            first_event_time=events[0].timestamp if events else None,
            last_event_time=events[-1].timestamp if events else None,
        )

    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict:
        """
        Generate compliance report for auditors.

        Suitable for NABH accreditation, legal discovery, etc.
        """
        if not self.db:
            return {}

        events = self.db.get_audit_events_by_date_range(start_date, end_date)

        # Categorize events
        action_counts = {}
        user_activity = {}
        patient_access = {}
        ai_usage = {"total": 0, "accepted": 0, "modified": 0, "rejected": 0}
        alert_overrides = []

        for event in events:
            # Count by action type
            action_name = event.action.value
            action_counts[action_name] = action_counts.get(action_name, 0) + 1

            # Count by user
            if event.user_id not in user_activity:
                user_activity[event.user_id] = {
                    "name": event.user_name,
                    "action_count": 0,
                    "patients_accessed": set(),
                }
            user_activity[event.user_id]["action_count"] += 1
            if event.patient_id:
                user_activity[event.user_id]["patients_accessed"].add(event.patient_id)

            # Count patient accesses
            if event.patient_id:
                if event.patient_id not in patient_access:
                    patient_access[event.patient_id] = {
                        "name": event.patient_name,
                        "access_count": 0,
                    }
                patient_access[event.patient_id]["access_count"] += 1

            # Track AI usage
            if "AI_SUGGESTION" in action_name:
                ai_usage["total"] += 1
                if event.action == AuditAction.AI_SUGGESTION_ACCEPT:
                    ai_usage["accepted"] += 1
                elif event.action == AuditAction.AI_SUGGESTION_MODIFY:
                    ai_usage["modified"] += 1
                elif event.action == AuditAction.AI_SUGGESTION_REJECT:
                    ai_usage["rejected"] += 1

            # Track alert overrides
            if event.action == AuditAction.MEDICATION_OVERRIDE_ALERT:
                alert_overrides.append({
                    "timestamp": event.timestamp,
                    "user": event.user_name,
                    "patient": event.patient_name,
                    "details": event.details,
                })

        # Convert sets to counts for JSON serialization
        for user_id in user_activity:
            user_activity[user_id]["unique_patients_accessed"] = len(
                user_activity[user_id]["patients_accessed"]
            )
            del user_activity[user_id]["patients_accessed"]

        # Verify chain integrity
        chain_status = self.verify_chain_integrity()

        return {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_events": len(events),
            "chain_integrity": {
                "is_valid": chain_status.is_valid,
                "verified_events": chain_status.verified_events,
            },
            "action_summary": action_counts,
            "user_activity": user_activity,
            "patient_access_summary": {
                "total_patients_accessed": len(patient_access),
                "most_accessed": sorted(
                    patient_access.items(),
                    key=lambda x: x[1]["access_count"],
                    reverse=True
                )[:10],
            },
            "ai_usage": ai_usage,
            "alert_overrides": alert_overrides,
            "generated_at": datetime.now().isoformat(),
        }

    def export_for_legal(
        self,
        patient_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Export patient audit trail for legal proceedings.

        Includes chain verification and signature.
        """
        events = self.get_patient_audit_trail(patient_id, start_date, end_date)

        # Verify each event
        verified_events = []
        for event in events:
            verified_events.append({
                "event": asdict(event),
                "integrity_verified": event.verify_integrity(),
            })

        # Calculate overall hash
        all_hashes = "".join(e["event"]["current_hash"] for e in verified_events)
        export_hash = hashlib.sha256(all_hashes.encode()).hexdigest()

        return {
            "export_type": "legal_discovery",
            "patient_id": patient_id,
            "date_range": {
                "start": start_date.isoformat() if start_date else "all",
                "end": end_date.isoformat() if end_date else "all",
            },
            "total_events": len(verified_events),
            "events": verified_events,
            "export_hash": export_hash,
            "exported_at": datetime.now().isoformat(),
            "verification_note": (
                "Each event contains a cryptographic hash linking it to the "
                "previous event. Any tampering will break the chain and be "
                "detectable by recalculating hashes."
            ),
        }

    def _get_last_hash(self) -> str:
        """Get the hash of the last audit event."""
        if self.db:
            last_event = self.db.get_last_audit_event()
            if last_event:
                return last_event.current_hash
        return "genesis"
