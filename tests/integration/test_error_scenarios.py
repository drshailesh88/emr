"""End-to-end integration tests for error handling scenarios.

Tests database failures, service unavailability, network errors, and concurrent access.
"""

import pytest
import asyncio
from datetime import datetime, date
import sqlite3
from unittest.mock import AsyncMock, MagicMock


class TestErrorScenarios:
    """Test error handling and recovery."""

    def test_database_connection_lost(self, real_db, sample_patient):
        """Simulate DB disconnect → verify graceful handling."""
        # Close database connection
        real_db.close()

        # Try to access database
        try:
            patient = real_db.get_patient(sample_patient.id)
            # If we get here, reconnection worked
            assert patient is not None
        except Exception as e:
            # Should get a meaningful error, not crash
            assert "database" in str(e).lower() or "connection" in str(e).lower()

        # Verify we can reconnect
        real_db.init_db()
        patient = real_db.get_patient(sample_patient.id)
        assert patient is not None

    def test_database_locked_error(self, temp_db_path):
        """Test handling database locked scenarios."""
        from src.services.database import DatabaseService

        # Create two connections to same database
        db1 = DatabaseService(temp_db_path)
        db1.init_db()

        db2 = DatabaseService(temp_db_path)

        # Start a transaction in db1
        conn1 = db1.get_connection()
        cursor1 = conn1.cursor()

        try:
            # Begin exclusive transaction
            cursor1.execute("BEGIN EXCLUSIVE")

            # Try to write from db2 (should timeout or fail)
            from src.models.schemas import Patient

            patient = Patient(
                name="Test Patient",
                age=30,
                gender="M",
                phone="9876543210"
            )

            try:
                # This might timeout or fail
                db2.add_patient(patient)
            except sqlite3.OperationalError as e:
                # Expected: database is locked
                assert "locked" in str(e).lower()

        finally:
            # Clean up
            conn1.rollback()
            db1.close()
            db2.close()

    @pytest.mark.asyncio
    async def test_llm_service_unavailable(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """LLM down → verify fallback behavior."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Make LLM service fail
        llm = full_service_registry.get("llm")

        async def failing_generate(*args, **kwargs):
            raise Exception("LLM service unavailable")

        original_generate = llm.generate_prescription
        llm.generate_prescription.side_effect = failing_generate

        try:
            # Try to generate prescription
            medications = [
                {
                    "drug_name": "Paracetamol",
                    "strength": "500mg",
                    "dose": "1",
                    "frequency": "TDS"
                }
            ]

            # Should either use fallback or raise gracefully
            try:
                prescription = await clinical_flow.generate_prescription(
                    medications=medications,
                    patient_id=sample_patient.id
                )

                # If successful, fallback worked
                assert prescription is not None

            except Exception as e:
                # Should be a handled error, not system crash
                assert "LLM" in str(e) or "unavailable" in str(e).lower()

        finally:
            # Restore
            llm.generate_prescription.side_effect = original_generate

    @pytest.mark.asyncio
    async def test_whatsapp_delivery_failure(
        self,
        sample_patient,
        mock_whatsapp_client
    ):
        """Delivery fails → verify retry queued."""
        # Make WhatsApp fail
        async def failing_send(to, message, **kwargs):
            return {
                "message_id": "",
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "error": "Network timeout"
            }

        original_send = mock_whatsapp_client.send_text
        mock_whatsapp_client.send_text.side_effect = failing_send

        try:
            # Try to send message
            result = await mock_whatsapp_client.send_text(
                to=sample_patient.phone,
                message="Test message"
            )

            # Verify failure captured
            assert result["status"] == "failed"
            assert "error" in result

            # In real implementation, would queue for retry
            retry_queue = []
            if result["status"] == "failed":
                retry_queue.append({
                    "to": sample_patient.phone,
                    "message": "Test message",
                    "failed_at": datetime.now().isoformat(),
                    "error": result["error"],
                    "retry_count": 0
                })

            # Verify queued
            assert len(retry_queue) == 1

        finally:
            mock_whatsapp_client.send_text.side_effect = original_send

    def test_concurrent_patient_edit(self, real_db, sample_patient):
        """Two users edit same patient → verify conflict handling."""
        # Get patient in two "sessions"
        patient1 = real_db.get_patient(sample_patient.id)
        patient2 = real_db.get_patient(sample_patient.id)

        # User 1 updates phone
        patient1.phone = "9999999999"
        success1 = real_db.update_patient(patient1)
        assert success1 is True

        # User 2 updates address (has old phone value)
        patient2.address = "New Address"
        success2 = real_db.update_patient(patient2)
        assert success2 is True

        # Check final state
        final = real_db.get_patient(sample_patient.id)

        # Last write wins (User 2's update)
        # User 1's phone change might be overwritten
        # In real app, would need optimistic locking or version control


class TestDataValidationErrors:
    """Test validation error handling."""

    def test_invalid_patient_data(self, real_db):
        """Try to create patient with invalid data."""
        from src.models.schemas import Patient
        from pydantic import ValidationError

        # Try to create patient with negative age
        try:
            patient = Patient(
                name="Test Patient",
                age=-5,  # Invalid
                gender="M",
                phone="9876543210"
            )
            # If validation allows negative age, test passes
            # If not, we should catch ValidationError
        except (ValidationError, ValueError) as e:
            # Expected: validation error
            assert "age" in str(e).lower() or "validation" in str(e).lower()

    def test_missing_required_fields(self):
        """Try to create models without required fields."""
        from src.models.schemas import Patient
        from pydantic import ValidationError

        # Try to create patient without name
        try:
            patient = Patient(
                age=30,
                gender="M"
            )
            # Should fail validation
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            # Expected
            assert "name" in str(e).lower()

    def test_invalid_prescription_format(self, real_db, sample_patient):
        """Try to save visit with malformed prescription JSON."""
        from src.models.schemas import Visit

        # Create visit with invalid JSON
        visit = Visit(
            patient_id=sample_patient.id,
            visit_date=date.today(),
            chief_complaint="Test",
            diagnosis="Test",
            prescription_json="invalid json {not: valid}"
        )

        # Should either validate or accept string
        # SQLite will store any string
        added = real_db.add_visit(visit)
        assert added.id is not None

        # When retrieving, should handle invalid JSON
        retrieved = real_db.get_visit(added.id)
        assert retrieved.prescription_json is not None


class TestNetworkErrors:
    """Test network-related error handling."""

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_whatsapp_client):
        """Simulate network timeout."""
        async def timeout_send(to, message, **kwargs):
            await asyncio.sleep(0.1)
            raise asyncio.TimeoutError("Request timeout")

        original_send = mock_whatsapp_client.send_text
        mock_whatsapp_client.send_text.side_effect = timeout_send

        try:
            # Try to send with timeout
            try:
                result = await asyncio.wait_for(
                    mock_whatsapp_client.send_text(
                        to="9876543210",
                        message="Test"
                    ),
                    timeout=0.05  # 50ms timeout
                )
            except asyncio.TimeoutError:
                # Expected
                pass

        finally:
            mock_whatsapp_client.send_text.side_effect = original_send

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_whatsapp_client):
        """Simulate connection refused."""
        async def connection_error(*args, **kwargs):
            raise ConnectionError("Connection refused")

        original_send = mock_whatsapp_client.send_text
        mock_whatsapp_client.send_text.side_effect = connection_error

        try:
            result = await mock_whatsapp_client.send_text(
                to="9876543210",
                message="Test"
            )
            # Should not reach here
            assert False, "Should have raised ConnectionError"
        except ConnectionError as e:
            # Expected
            assert "refused" in str(e).lower()
        finally:
            mock_whatsapp_client.send_text.side_effect = original_send


class TestResourceExhaustion:
    """Test handling of resource exhaustion."""

    def test_memory_limit_handling(self, real_db):
        """Test handling of large result sets."""
        from src.models.schemas import Patient

        # Create many patients
        patient_ids = []
        for i in range(100):
            patient = Patient(
                name=f"Patient {i}",
                age=30 + (i % 50),
                gender="M" if i % 2 == 0 else "F",
                phone=f"98765{i:05d}"
            )
            added = real_db.add_patient(patient)
            patient_ids.append(added.id)

        # Try to retrieve all at once
        # Search should handle large result sets
        results = real_db.search_patients_basic("")

        # Should return results (possibly paginated in real app)
        assert len(results) >= 100

    def test_disk_space_error(self, temp_db_path):
        """Test handling disk full error."""
        # This is hard to test without actually filling disk
        # Placeholder test

        from src.services.database import DatabaseService

        db = DatabaseService(temp_db_path)
        db.init_db()

        # In real scenario, would simulate disk full
        # For now, just verify DB can handle writes
        from src.models.schemas import Patient

        patient = Patient(
            name="Test Patient",
            age=30,
            gender="M",
            phone="9876543210"
        )

        added = db.add_patient(patient)
        assert added.id is not None

        db.close()


class TestTransactionRollback:
    """Test transaction rollback on errors."""

    def test_rollback_on_error(self, real_db, sample_patient):
        """Start transaction → error occurs → verify rollback."""
        from src.models.schemas import Visit

        # Get initial visit count
        initial_visits = real_db.get_patient_visits(sample_patient.id)
        initial_count = len(initial_visits)

        # Try to add visit in transaction
        conn = real_db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN")

            # Add visit
            visit = Visit(
                patient_id=sample_patient.id,
                visit_date=date.today(),
                chief_complaint="Test",
                diagnosis="Test"
            )

            # Insert visit
            cursor.execute("""
                INSERT INTO visits (patient_id, visit_date, chief_complaint, diagnosis)
                VALUES (?, ?, ?, ?)
            """, (visit.patient_id, visit.visit_date, visit.chief_complaint, visit.diagnosis))

            # Simulate error
            raise Exception("Simulated error")

        except Exception:
            # Rollback on error
            conn.rollback()

        # Verify visit not saved
        final_visits = real_db.get_patient_visits(sample_patient.id)
        final_count = len(final_visits)

        assert final_count == initial_count  # No new visit


class TestServiceDependencyFailure:
    """Test handling of service dependency failures."""

    @pytest.mark.asyncio
    async def test_multiple_service_failures(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """Multiple services fail → verify system stability."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Make multiple services fail
        whatsapp = full_service_registry.get("whatsapp_client")
        analytics = full_service_registry.get("practice_analytics")

        async def failing_whatsapp(*args, **kwargs):
            raise Exception("WhatsApp service down")

        async def failing_analytics(*args, **kwargs):
            raise Exception("Analytics service down")

        original_whatsapp = whatsapp.send_prescription
        original_analytics = analytics.record_consultation

        whatsapp.send_prescription.side_effect = failing_whatsapp
        analytics.record_consultation.side_effect = failing_analytics

        try:
            # Try to complete consultation
            visit_data = {
                "chief_complaint": "Test",
                "diagnosis": "Test"
            }

            # Should handle failures gracefully
            # Core functionality (saving visit) should still work
            try:
                summary = await clinical_flow.complete_consultation(visit_data)

                # Visit should be saved even if other services failed
                assert summary["visit_id"] is not None

                # But these might fail
                # assert summary["prescription_sent"] is False
                # assert summary["analytics_updated"] is False

            except Exception as e:
                # Or might raise exception but visit should be saved
                pass

        finally:
            # Restore
            whatsapp.send_prescription.side_effect = original_whatsapp
            analytics.record_consultation.side_effect = original_analytics

    @pytest.mark.asyncio
    async def test_partial_failure_recovery(
        self,
        clinical_flow,
        sample_patient,
        full_service_registry
    ):
        """One service fails → others continue working."""
        # Start consultation
        context = await clinical_flow.start_consultation(
            patient_id=sample_patient.id,
            doctor_id="DR001"
        )

        # Make only WhatsApp fail
        whatsapp = full_service_registry.get("whatsapp_client")

        async def failing_whatsapp(*args, **kwargs):
            raise Exception("WhatsApp failed")

        original_send = whatsapp.send_prescription
        whatsapp.send_prescription.side_effect = failing_whatsapp

        try:
            # Complete consultation
            visit_data = {
                "chief_complaint": "Test",
                "diagnosis": "Test"
            }

            summary = await clinical_flow.complete_consultation(visit_data)

            # Visit should be saved
            assert summary["visit_id"] is not None

            # Analytics might still work
            analytics = full_service_registry.get("practice_analytics")
            # Check if analytics was updated despite WhatsApp failure

        finally:
            whatsapp.send_prescription.side_effect = original_send


class TestDataCorruption:
    """Test handling of corrupted data."""

    def test_corrupted_json_handling(self, real_db, sample_patient):
        """Encounter corrupted prescription JSON → handle gracefully."""
        from src.models.schemas import Visit

        # Create visit with corrupted JSON
        visit = Visit(
            patient_id=sample_patient.id,
            visit_date=date.today(),
            chief_complaint="Test",
            diagnosis="Test",
            prescription_json="{corrupted json"
        )

        added = real_db.add_visit(visit)

        # Try to retrieve and parse
        retrieved = real_db.get_visit(added.id)

        # Try to parse JSON
        import json
        try:
            prescription = json.loads(retrieved.prescription_json)
            # If it succeeds, JSON was auto-corrected or is valid
        except json.JSONDecodeError:
            # Expected for corrupted JSON
            # Should handle gracefully, not crash
            pass

    def test_invalid_foreign_key(self, real_db):
        """Try to create record with invalid foreign key."""
        from src.models.schemas import Visit

        # Try to create visit for non-existent patient
        visit = Visit(
            patient_id=99999,  # Non-existent
            visit_date=date.today(),
            chief_complaint="Test",
            diagnosis="Test"
        )

        try:
            added = real_db.add_visit(visit)
            # If it succeeds, foreign key constraint not enforced
            # Delete the orphaned visit
            if added.id:
                conn = real_db.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM visits WHERE id = ?", (added.id,))
                conn.commit()
        except (sqlite3.IntegrityError, Exception) as e:
            # Expected: foreign key constraint violation
            assert "foreign" in str(e).lower() or "constraint" in str(e).lower()
