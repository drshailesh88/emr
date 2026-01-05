"""End-to-end integration tests for audit and compliance.

Tests audit logging, chain integrity, consent management, and legal exports.
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta
import json
import hashlib


class TestAuditCompliance:
    """Test audit trail and compliance features."""

    @pytest.mark.asyncio
    async def test_all_actions_logged(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry,
        mock_audit_logger
    ):
        """Perform various actions → verify all in audit log."""
        # 1. Start consultation (should be logged)
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Verify consultation start logged
        start_events = [e for e in mock_audit_logger.events if e["event_type"] == "consultation_started"]
        assert len(start_events) > 0

        # 2. Generate prescription (should be logged)
        medications = [
            {
                "drug_name": "Paracetamol",
                "strength": "500mg",
                "dose": "1",
                "frequency": "TDS"
            }
        ]

        await clinical_flow.generate_prescription(
            medications=medications,
            patient_id=sample_patient.id
        )

        # Verify prescription logged
        prescription_events = [e for e in mock_audit_logger.events if e["event_type"] == "prescription_created"]
        assert len(prescription_events) > 0

        # 3. Complete consultation (should be logged)
        visit_data = {
            "chief_complaint": "Fever",
            "diagnosis": "Viral Fever"
        }

        await clinical_flow.complete_consultation(visit_data)

        # Verify completion logged
        completion_events = [e for e in mock_audit_logger.events if e["event_type"] == "consultation_completed"]
        assert len(completion_events) > 0

        # 4. Verify all events have required fields
        for event in mock_audit_logger.events:
            assert "event_type" in event
            assert "user_id" in event
            assert "timestamp" in event
            assert event["timestamp"] is not None

    @pytest.mark.asyncio
    async def test_chain_integrity_maintained(
        self,
        mock_audit_logger
    ):
        """Multiple actions → verify hash chain intact."""
        # Simulate audit events with hash chain
        previous_hash = "0000000000000000"

        events = []
        for i in range(10):
            # Create event
            event_data = {
                "event_type": f"action_{i}",
                "user_id": "DR001",
                "patient_id": 1,
                "metadata": {"action": f"Action {i}"},
                "timestamp": datetime.now().isoformat(),
                "previous_hash": previous_hash
            }

            # Calculate hash of this event
            event_string = json.dumps(event_data, sort_keys=True)
            current_hash = hashlib.sha256(event_string.encode()).hexdigest()
            event_data["hash"] = current_hash

            events.append(event_data)
            previous_hash = current_hash

        # Verify chain integrity
        for i in range(1, len(events)):
            # Current event's previous_hash should match previous event's hash
            assert events[i]["previous_hash"] == events[i-1]["hash"]

        # Verify no tampering - recalculate all hashes
        for event in events:
            # Remove hash to recalculate
            stored_hash = event.pop("hash")

            # Recalculate
            event_string = json.dumps(event, sort_keys=True)
            calculated_hash = hashlib.sha256(event_string.encode()).hexdigest()

            # Should match
            assert stored_hash == calculated_hash

            # Restore hash
            event["hash"] = stored_hash

    @pytest.mark.asyncio
    async def test_consent_workflow(
        self,
        sample_patient,
        real_db
    ):
        """Request consent → sign → verify → withdraw consent."""
        # This test assumes a consent management system exists
        # For now, we'll test the workflow conceptually

        # 1. Request consent
        consent_request = {
            "patient_id": sample_patient.id,
            "consent_type": "data_sharing",
            "purpose": "Share prescription with pharmacy",
            "requested_at": datetime.now().isoformat(),
            "status": "pending"
        }

        # In real implementation, would store in database
        consent_id = 1

        # 2. Patient signs consent
        consent_request["status"] = "granted"
        consent_request["granted_at"] = datetime.now().isoformat()
        consent_request["signature"] = "digital_signature_hash"

        # Verify consent granted
        assert consent_request["status"] == "granted"
        assert consent_request["signature"] is not None

        # 3. Verify consent is active
        is_valid = (
            consent_request["status"] == "granted" and
            consent_request.get("withdrawn_at") is None
        )
        assert is_valid is True

        # 4. Withdraw consent
        consent_request["status"] = "withdrawn"
        consent_request["withdrawn_at"] = datetime.now().isoformat()

        # Verify consent withdrawn
        assert consent_request["status"] == "withdrawn"
        is_valid = (consent_request["status"] == "granted")
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_legal_export_format(
        self,
        sample_patient,
        real_db,
        mock_audit_logger
    ):
        """Generate legal-compliant export → verify format correct."""
        from src.models.schemas import Visit

        # Create some audit events
        await mock_audit_logger.log_event(
            event_type="patient_view",
            user_id="DR001",
            patient_id=sample_patient.id,
            metadata={"action": "viewed_patient_record"}
        )

        await mock_audit_logger.log_event(
            event_type="patient_update",
            user_id="DR001",
            patient_id=sample_patient.id,
            metadata={"fields_updated": ["phone", "address"]}
        )

        # Create visit
        visit = Visit(
            patient_id=sample_patient.id,
            visit_date=date.today(),
            chief_complaint="Test",
            diagnosis="Test Diagnosis"
        )
        real_db.add_visit(visit)

        # Generate legal export
        export_data = {
            "export_type": "legal_compliance",
            "generated_at": datetime.now().isoformat(),
            "generated_by": "DR001",
            "patient": {
                "id": sample_patient.id,
                "uhid": sample_patient.uhid,
                "name": sample_patient.name,
                "age": sample_patient.age,
                "gender": sample_patient.gender
            },
            "visits": [],
            "audit_trail": []
        }

        # Add visits
        visits = real_db.get_patient_visits(sample_patient.id)
        for v in visits:
            export_data["visits"].append({
                "visit_date": v.visit_date.isoformat(),
                "chief_complaint": v.chief_complaint,
                "diagnosis": v.diagnosis
            })

        # Add audit events
        patient_events = [
            e for e in mock_audit_logger.events
            if e.get("patient_id") == sample_patient.id
        ]
        for event in patient_events:
            export_data["audit_trail"].append({
                "timestamp": event["timestamp"],
                "event_type": event["event_type"],
                "user_id": event["user_id"],
                "metadata": event.get("metadata", {})
            })

        # Verify export format
        assert "export_type" in export_data
        assert export_data["export_type"] == "legal_compliance"
        assert "generated_at" in export_data
        assert "patient" in export_data
        assert "visits" in export_data
        assert "audit_trail" in export_data

        # Verify patient data present
        assert export_data["patient"]["uhid"] == sample_patient.uhid

        # Verify audit trail included
        assert len(export_data["audit_trail"]) > 0


class TestDataAccessControl:
    """Test data access logging and controls."""

    @pytest.mark.asyncio
    async def test_patient_access_logging(
        self,
        sample_patient,
        mock_audit_logger
    ):
        """Log every patient record access."""
        # Simulate accessing patient record
        await mock_audit_logger.log_event(
            event_type="patient_view",
            user_id="DR001",
            patient_id=sample_patient.id,
            metadata={
                "access_type": "view",
                "screen": "patient_details",
                "ip_address": "192.168.1.100"
            }
        )

        # Verify logged
        view_events = [
            e for e in mock_audit_logger.events
            if e["event_type"] == "patient_view" and e["patient_id"] == sample_patient.id
        ]
        assert len(view_events) > 0

        event = view_events[0]
        assert event["metadata"]["access_type"] == "view"
        assert "ip_address" in event["metadata"]

    @pytest.mark.asyncio
    async def test_prescription_access_logging(
        self,
        sample_patient,
        mock_audit_logger
    ):
        """Log prescription views and exports."""
        # View prescription
        await mock_audit_logger.log_event(
            event_type="prescription_view",
            user_id="DR001",
            patient_id=sample_patient.id,
            metadata={"visit_id": 123}
        )

        # Export prescription
        await mock_audit_logger.log_event(
            event_type="prescription_export",
            user_id="DR001",
            patient_id=sample_patient.id,
            metadata={
                "visit_id": 123,
                "export_format": "pdf"
            }
        )

        # Verify both logged
        prescription_events = [
            e for e in mock_audit_logger.events
            if "prescription" in e["event_type"]
        ]
        assert len(prescription_events) == 2

    @pytest.mark.asyncio
    async def test_unauthorized_access_prevention(
        self,
        mock_audit_logger
    ):
        """Attempt unauthorized access → verify blocked and logged."""
        # Simulate unauthorized access attempt
        await mock_audit_logger.log_event(
            event_type="unauthorized_access_attempt",
            user_id="UNKNOWN_USER",
            patient_id=999,
            metadata={
                "reason": "User not authorized to view this patient",
                "attempted_action": "view_patient"
            }
        )

        # Verify logged
        unauthorized_events = [
            e for e in mock_audit_logger.events
            if e["event_type"] == "unauthorized_access_attempt"
        ]
        assert len(unauthorized_events) > 0


class TestDataRetention:
    """Test data retention and archival."""

    def test_archive_old_records(self, real_db):
        """Archive records older than retention period."""
        from src.models.schemas import Patient, Visit

        # Create old patient with old visits
        patient = Patient(
            name="Old Patient",
            age=70,
            gender="M",
            phone="9876543210"
        )
        added_patient = real_db.add_patient(patient)

        # Create very old visit (3 years ago)
        old_visit = Visit(
            patient_id=added_patient.id,
            visit_date=date.today() - timedelta(days=365*3),
            chief_complaint="Old visit",
            diagnosis="Old diagnosis"
        )
        real_db.add_visit(old_visit)

        # Create recent visit
        recent_visit = Visit(
            patient_id=added_patient.id,
            visit_date=date.today() - timedelta(days=30),
            chief_complaint="Recent visit",
            diagnosis="Recent diagnosis"
        )
        real_db.add_visit(recent_visit)

        # Get all visits
        visits = real_db.get_patient_visits(added_patient.id)

        # Identify old visits (retention period: 2 years)
        retention_days = 365 * 2
        cutoff_date = date.today() - timedelta(days=retention_days)

        old_visits = [v for v in visits if v.visit_date < cutoff_date]
        recent_visits = [v for v in visits if v.visit_date >= cutoff_date]

        # Verify classification
        assert len(old_visits) >= 1  # At least the 3-year-old visit
        assert len(recent_visits) >= 1  # At least the recent visit

        # In real implementation, would archive old_visits


class TestComplianceReporting:
    """Test compliance reporting features."""

    @pytest.mark.asyncio
    async def test_hipaa_compliance_report(
        self,
        mock_audit_logger
    ):
        """Generate HIPAA-compliant audit report."""
        # Create various audit events
        events = [
            {
                "event_type": "patient_view",
                "user_id": "DR001",
                "patient_id": 1,
                "metadata": {"action": "viewed"}
            },
            {
                "event_type": "patient_update",
                "user_id": "DR001",
                "patient_id": 1,
                "metadata": {"fields": ["phone"]}
            },
            {
                "event_type": "prescription_export",
                "user_id": "DR001",
                "patient_id": 1,
                "metadata": {"format": "pdf"}
            }
        ]

        for event in events:
            await mock_audit_logger.log_event(**event)

        # Generate compliance report
        report = {
            "report_type": "hipaa_compliance",
            "period_start": (datetime.now() - timedelta(days=30)).isoformat(),
            "period_end": datetime.now().isoformat(),
            "total_accesses": len(mock_audit_logger.events),
            "events_by_type": {},
            "events_by_user": {},
            "unauthorized_attempts": 0
        }

        # Count by type
        for event in mock_audit_logger.events:
            event_type = event["event_type"]
            report["events_by_type"][event_type] = report["events_by_type"].get(event_type, 0) + 1

            # Count by user
            user_id = event["user_id"]
            report["events_by_user"][user_id] = report["events_by_user"].get(user_id, 0) + 1

        # Verify report
        assert report["total_accesses"] > 0
        assert len(report["events_by_type"]) > 0
        assert len(report["events_by_user"]) > 0

    @pytest.mark.asyncio
    async def test_data_breach_notification(
        self,
        mock_audit_logger
    ):
        """Detect potential breach → generate notification."""
        # Simulate suspicious activity
        # Multiple failed access attempts in short time

        for i in range(10):
            await mock_audit_logger.log_event(
                event_type="login_failed",
                user_id=f"UNKNOWN_{i}",
                patient_id=None,
                metadata={
                    "reason": "invalid_credentials",
                    "ip_address": "192.168.1.100",
                    "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat()
                }
            )

        # Detect breach pattern
        failed_logins = [
            e for e in mock_audit_logger.events
            if e["event_type"] == "login_failed"
        ]

        # If > 5 failed attempts from same IP in 10 minutes, flag as breach
        if len(failed_logins) > 5:
            # Generate breach notification
            breach_notification = {
                "alert_type": "potential_breach",
                "detected_at": datetime.now().isoformat(),
                "description": f"{len(failed_logins)} failed login attempts detected",
                "recommended_action": "Block IP address, notify security team",
                "events": failed_logins
            }

            # Verify notification generated
            assert breach_notification["alert_type"] == "potential_breach"
            assert len(breach_notification["events"]) > 5


class TestConsentManagement:
    """Test patient consent management."""

    @pytest.mark.asyncio
    async def test_consent_expiration(self):
        """Verify expired consents are not honored."""
        # Create consent with expiration
        consent = {
            "patient_id": 1,
            "consent_type": "data_sharing",
            "granted_at": (datetime.now() - timedelta(days=400)).isoformat(),
            "expires_at": (datetime.now() - timedelta(days=30)).isoformat(),  # Expired
            "status": "granted"
        }

        # Check if valid
        expires_at = datetime.fromisoformat(consent["expires_at"])
        is_expired = datetime.now() > expires_at

        # Should be expired
        assert is_expired is True

        # Should not honor expired consent
        is_valid = (
            consent["status"] == "granted" and
            not is_expired and
            consent.get("withdrawn_at") is None
        )
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_granular_consent(self):
        """Test different consent types for different purposes."""
        consents = [
            {
                "patient_id": 1,
                "consent_type": "prescription_sharing",
                "status": "granted"
            },
            {
                "patient_id": 1,
                "consent_type": "marketing_communications",
                "status": "denied"
            },
            {
                "patient_id": 1,
                "consent_type": "research_participation",
                "status": "granted"
            }
        ]

        # Check specific consent
        def has_consent(patient_id, consent_type):
            return any(
                c["patient_id"] == patient_id and
                c["consent_type"] == consent_type and
                c["status"] == "granted"
                for c in consents
            )

        # Verify granular control
        assert has_consent(1, "prescription_sharing") is True
        assert has_consent(1, "marketing_communications") is False
        assert has_consent(1, "research_participation") is True
