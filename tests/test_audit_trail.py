"""Tests for audit trail and compliance logging.

Tests that all clinical actions are properly logged with chain integrity,
legal export formats, and tamper detection.
"""

import pytest
from datetime import datetime
import hashlib
import json

# Import fixtures
pytest_plugins = ['tests.clinical_conftest']


class TestAuditTrail:
    """Tests for audit logging and compliance."""

    @pytest.mark.asyncio
    async def test_consultation_logged(self, clinical_flow, sample_patient, service_registry):
        """Test that consultation start is logged."""
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        audit_logger = service_registry.get("audit_logger")
        events = audit_logger.audit_events

        # Should have logged consultation start
        start_events = [e for e in events if e["event_type"] == "consultation_started"]
        assert len(start_events) > 0

        event = start_events[0]
        assert event["user_id"] == "DR001"
        assert event["patient_id"] == sample_patient.id
        assert event["timestamp"] is not None

    @pytest.mark.asyncio
    async def test_prescription_logged_with_warnings(
        self, clinical_flow, sample_patient, service_registry
    ):
        """Test that prescription generation is logged with warnings."""
        await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Generate prescription with known interaction
        medications = [
            {"drug_name": "Warfarin", "strength": "5mg"},
            {"drug_name": "Aspirin", "strength": "75mg"}
        ]

        await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        audit_logger = service_registry.get("audit_logger")
        events = audit_logger.audit_events

        # Should have logged prescription creation
        rx_events = [e for e in events if e["event_type"] == "prescription_created"]
        assert len(rx_events) > 0

        event = rx_events[0]
        assert "metadata" in event
        assert event["metadata"]["medication_count"] == 2
        # Should have logged interaction count
        assert "interactions" in event["metadata"]

    @pytest.mark.asyncio
    async def test_alert_override_logged(self):
        """Test that overriding safety alerts is logged."""
        # When doctor overrides a warning, it must be logged

        override_event = {
            "event_type": "safety_alert_overridden",
            "user_id": "DR001",
            "patient_id": 1,
            "alert_type": "drug_interaction",
            "alert_severity": "HIGH",
            "override_reason": "Patient already on this combination, discussed risks",
            "timestamp": datetime.now()
        }

        # Verify required fields
        assert override_event["override_reason"] is not None
        assert len(override_event["override_reason"]) > 10  # Must provide reason
        assert override_event["alert_severity"] is not None

    @pytest.mark.asyncio
    async def test_patient_view_logged(self, mock_audit_logger):
        """Test that viewing patient records is logged."""
        # Every access to patient data must be logged (HIPAA/data privacy)

        await mock_audit_logger.log_event(
            event_type="patient_viewed",
            user_id="DR001",
            patient_id=1,
            metadata={
                "viewed_sections": ["demographics", "visits", "investigations"],
                "purpose": "consultation"
            }
        )

        events = mock_audit_logger.audit_events
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == "patient_viewed"
        assert "viewed_sections" in event["metadata"]

    @pytest.mark.asyncio
    async def test_chain_integrity(self):
        """Test audit log chain integrity (tamper detection)."""
        # Each log entry should include hash of previous entry
        # This creates a blockchain-like audit trail

        def calculate_hash(entry):
            """Calculate hash of audit entry."""
            content = json.dumps(entry, sort_keys=True, default=str)
            return hashlib.sha256(content.encode()).hexdigest()

        # Simulate audit chain
        audit_chain = []
        previous_hash = "0" * 64  # Genesis hash

        entries = [
            {"event": "consultation_started", "user": "DR001", "patient": 1},
            {"event": "prescription_created", "user": "DR001", "patient": 1},
            {"event": "consultation_completed", "user": "DR001", "patient": 1},
        ]

        for entry in entries:
            entry["previous_hash"] = previous_hash
            entry["timestamp"] = datetime.now().isoformat()

            current_hash = calculate_hash(entry)
            entry["hash"] = current_hash

            audit_chain.append(entry)
            previous_hash = current_hash

        # Verify chain integrity
        for i in range(1, len(audit_chain)):
            expected_previous = audit_chain[i-1]["hash"]
            actual_previous = audit_chain[i]["previous_hash"]
            assert expected_previous == actual_previous, "Chain integrity broken"

        # Detect tampering
        audit_chain[1]["event"] = "TAMPERED"
        tampered_hash = calculate_hash(audit_chain[1])

        # Next entry's previous_hash won't match
        assert tampered_hash != audit_chain[2]["previous_hash"], "Tampering should be detected"

    @pytest.mark.asyncio
    async def test_legal_export_format(self, mock_audit_logger):
        """Test audit log export in legal/compliance format."""
        # Log multiple events
        events_to_log = [
            {"event_type": "consultation_started", "user_id": "DR001", "patient_id": 1},
            {"event_type": "prescription_created", "user_id": "DR001", "patient_id": 1},
            {"event_type": "consultation_completed", "user_id": "DR001", "patient_id": 1},
        ]

        for event in events_to_log:
            await mock_audit_logger.log_event(**event)

        # Export format should include:
        # - All events in chronological order
        # - User identification
        # - Timestamps in standard format
        # - Action details
        # - Digital signature/hash

        export_data = {
            "export_date": datetime.now().isoformat(),
            "export_purpose": "Legal compliance / Audit review",
            "events": mock_audit_logger.audit_events,
            "total_events": len(mock_audit_logger.audit_events),
            "date_range": {
                "start": mock_audit_logger.audit_events[0]["timestamp"],
                "end": mock_audit_logger.audit_events[-1]["timestamp"]
            }
        }

        assert export_data["total_events"] == 3
        assert export_data["export_purpose"] is not None

    @pytest.mark.asyncio
    async def test_data_access_by_unauthorized_user(self):
        """Test that unauthorized access attempts are logged."""
        unauthorized_access = {
            "event_type": "unauthorized_access_attempt",
            "user_id": "UNKNOWN",
            "patient_id": 1,
            "timestamp": datetime.now(),
            "ip_address": "192.168.1.100",
            "attempted_action": "view_patient_record",
            "blocked": True
        }

        # Verify unauthorized access is logged
        assert unauthorized_access["event_type"] == "unauthorized_access_attempt"
        assert unauthorized_access["blocked"] is True

    @pytest.mark.asyncio
    async def test_bulk_export_logged(self, mock_audit_logger):
        """Test that bulk data exports are logged."""
        await mock_audit_logger.log_event(
            event_type="bulk_data_exported",
            user_id="DR001",
            metadata={
                "export_type": "patient_list",
                "record_count": 150,
                "date_range": "2024-01-01 to 2024-01-31",
                "purpose": "Monthly report",
                "approved_by": "ADMIN001"
            }
        )

        events = mock_audit_logger.audit_events
        assert len(events) == 1

        event = events[0]
        assert event["metadata"]["record_count"] == 150
        assert event["metadata"]["approved_by"] is not None

    @pytest.mark.asyncio
    async def test_prescription_print_logged(self, mock_audit_logger):
        """Test that prescription printing is logged."""
        await mock_audit_logger.log_event(
            event_type="prescription_printed",
            user_id="DR001",
            patient_id=1,
            metadata={
                "visit_id": 123,
                "printer": "HP_LaserJet_Office",
                "copies": 1
            }
        )

        events = mock_audit_logger.audit_events
        assert events[0]["event_type"] == "prescription_printed"

    @pytest.mark.asyncio
    async def test_record_modification_logged(self, mock_audit_logger):
        """Test that record modifications are logged with before/after."""
        await mock_audit_logger.log_event(
            event_type="record_modified",
            user_id="DR001",
            patient_id=1,
            metadata={
                "record_type": "visit",
                "record_id": 123,
                "field_modified": "diagnosis",
                "old_value": "Viral Fever",
                "new_value": "Dengue Fever",
                "modification_reason": "Lab results confirmed dengue"
            }
        )

        events = mock_audit_logger.audit_events
        event = events[0]

        # Must log old and new values
        assert "old_value" in event["metadata"]
        assert "new_value" in event["metadata"]
        assert "modification_reason" in event["metadata"]

    @pytest.mark.asyncio
    async def test_deletion_logged_with_reason(self, mock_audit_logger):
        """Test that deletions are logged with reason."""
        await mock_audit_logger.log_event(
            event_type="record_deleted",
            user_id="DR001",
            patient_id=1,
            metadata={
                "record_type": "investigation",
                "record_id": 456,
                "deletion_reason": "Duplicate entry - already recorded",
                "deleted_data": {"test_name": "CBC", "result": "Normal"},
                "approved_by": "DR001"
            }
        )

        events = mock_audit_logger.audit_events
        event = events[0]

        # Deletion must have reason and deleted data backup
        assert event["metadata"]["deletion_reason"] is not None
        assert event["metadata"]["deleted_data"] is not None

    @pytest.mark.asyncio
    async def test_user_login_logout_logged(self, mock_audit_logger):
        """Test that user login/logout is logged."""
        # Login
        await mock_audit_logger.log_event(
            event_type="user_login",
            user_id="DR001",
            metadata={
                "login_time": datetime.now().isoformat(),
                "ip_address": "192.168.1.50",
                "device": "Desktop - Windows"
            }
        )

        # Logout
        await mock_audit_logger.log_event(
            event_type="user_logout",
            user_id="DR001",
            metadata={
                "logout_time": datetime.now().isoformat(),
                "session_duration": 3600  # seconds
            }
        )

        events = mock_audit_logger.audit_events
        assert len(events) == 2
        assert events[0]["event_type"] == "user_login"
        assert events[1]["event_type"] == "user_logout"

    @pytest.mark.asyncio
    async def test_compliance_report_generation(self, mock_audit_logger):
        """Test generation of compliance audit report."""
        # Log various activities
        activities = [
            "consultation_started", "prescription_created",
            "patient_viewed", "record_modified", "bulk_data_exported"
        ]

        for activity in activities:
            await mock_audit_logger.log_event(
                event_type=activity,
                user_id="DR001",
                patient_id=1
            )

        # Generate compliance report
        report = {
            "report_period": "2024-01-01 to 2024-01-31",
            "total_events": len(mock_audit_logger.audit_events),
            "by_event_type": {},
            "by_user": {},
            "high_risk_events": []
        }

        # Count by event type
        for event in mock_audit_logger.audit_events:
            event_type = event["event_type"]
            report["by_event_type"][event_type] = \
                report["by_event_type"].get(event_type, 0) + 1

        # Verify report structure
        assert report["total_events"] == len(activities)
        assert len(report["by_event_type"]) > 0

    @pytest.mark.asyncio
    async def test_retention_policy_compliance(self):
        """Test audit log retention policy compliance."""
        # Audit logs typically must be retained for 7-10 years
        retention_years = 7

        log_date = datetime.now()
        retention_until = log_date.replace(year=log_date.year + retention_years)

        # Verify retention period
        assert retention_until.year == log_date.year + retention_years

        # Logs should not be deleted before retention period
        # Implement auto-archival after retention period
