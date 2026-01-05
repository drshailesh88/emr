# DocAssist EMR - Integration Tests

Comprehensive end-to-end integration tests for the DocAssist EMR system.

## Overview

These tests verify that the **complete system** works correctly when all services are wired together. Unlike unit tests that test individual components in isolation, integration tests verify:

- Complete user workflows from start to finish
- Service interactions and data flow
- Database state changes
- External service integrations (WhatsApp, voice, etc.)
- Error handling and recovery
- Audit trail and compliance

## Test Architecture

### Test Infrastructure

**conftest.py** - Integration Test Fixtures
- ✅ Real SQLite database (temporary, cleaned up after each test)
- ✅ Mock LLM service with realistic responses
- ✅ Mock WhatsApp client that logs messages
- ✅ Mock voice capture and speech-to-text
- ✅ Mock clinical services (NLP, interaction checker, red flag detector)
- ✅ Full ServiceRegistry with all services wired
- ✅ Clinical flow orchestrator ready to use
- ✅ Helper assertions for common verifications

### Test Modules

## 1. Consultation Flow Tests (`test_consultation_flow.py`)

**Complete end-to-end consultation workflows**

### TestFullConsultationFlow

#### ✅ `test_complete_consultation_happy_path`
Tests the complete consultation lifecycle:
1. Create patient
2. Start consultation
3. Process voice input (ambient listening)
4. Extract SOAP note
5. Generate prescription
6. Check drug interactions
7. Save visit to database
8. Send prescription via WhatsApp
9. Verify audit trail logged
10. Verify analytics updated

**Verifies:**
- All services integrate correctly
- Data flows through system
- Database state correct
- External messages sent
- Audit events logged

#### ✅ `test_consultation_with_drug_interaction`
Tests interaction detection and alerts:
- Prescribe Aspirin + Warfarin
- Verify interaction detected
- Verify alert shown to doctor
- Verify interaction logged in context

#### ✅ `test_consultation_with_red_flag`
Tests red flag detection:
- Patient mentions "chest pain"
- Verify red flag detected
- Verify alert escalated
- Verify logged in consultation context

#### ✅ `test_consultation_cancellation`
Tests cancellation workflow:
- Start consultation
- Cancel before completion
- Verify context closed
- Verify cancellation logged
- Verify no visit saved

#### ✅ `test_consultation_error_recovery`
Tests recovery from mid-consultation errors:
- Start consultation
- Interaction checker fails
- Verify system continues
- Verify error handled gracefully

### TestConsultationWithVitals

#### ✅ `test_vitals_extraction_from_speech`
Tests extracting vitals from ambient speech:
- Process speech: "BP is 140 over 90"
- Verify BP extracted by NLP
- Verify added to context

### TestMultiplePatientConsultations

#### ✅ `test_sequential_consultations`
Tests multiple consultations in sequence:
- Complete consultation for Patient A
- Complete consultation for Patient B
- Verify both visits saved
- Verify analytics tracked both

### TestConsultationWithFollowUp

#### ✅ `test_follow_up_reminder_scheduled`
Tests follow-up scheduling:
- Complete consultation with follow-up date
- Verify reminder scheduled
- Verify reminder contains correct info

---

## 2. Voice to Prescription Tests (`test_voice_to_prescription.py`)

**Voice processing pipeline from audio to prescription**

### TestVoiceToPrescription

#### ✅ `test_hindi_voice_to_prescription`
Tests Hindi speech → transcription → SOAP → prescription:
- Process Hindi audio
- Verify transcription in Hindi/English
- Generate prescription from notes

#### ✅ `test_english_voice_to_prescription`
Tests English speech processing:
- Process English audio
- Verify entity extraction (fever, headache)
- Verify symptoms identified

#### ✅ `test_hinglish_voice_to_prescription`
Tests code-mixed (Hinglish) speech:
- Process mixed Hindi-English audio
- Verify both languages handled
- Verify entities extracted

#### ✅ `test_voice_with_vitals`
Tests vital sign extraction from speech:
- Speech: "BP is 140 over 90"
- Verify vitals extracted
- Verify structured in entities

#### ✅ `test_voice_with_medications`
Tests medication extraction from speech:
- Speech: "Give Paracetamol 500mg TDS"
- Verify medication extracted
- Verify dosage captured

### TestVoiceSOAPExtraction

#### ✅ `test_soap_extraction_from_conversation`
Tests SOAP note generation from multiple speech segments:
- Process multiple conversation chunks
- Verify all accumulated
- Extract structured SOAP note

### TestMultilingualVoice

#### ✅ `test_language_switching_mid_consultation`
Tests handling language switches:
- Start in Hindi
- Switch to English mid-conversation
- Verify both captured

### TestVoiceErrorHandling

#### ✅ `test_speech_recognition_failure`
Tests handling speech recognition failures:
- STT service fails
- Verify graceful error handling

#### ✅ `test_empty_audio_handling`
Tests handling empty/invalid audio

### TestRealTimeVoiceProcessing

#### ✅ `test_streaming_voice_updates`
Tests real-time chunked audio processing:
- Process multiple audio chunks
- Verify all transcribed
- Verify notes accumulate

---

## 3. Patient Lifecycle Tests (`test_patient_lifecycle.py`)

**Complete patient journey from registration to long-term care**

### TestPatientLifecycle

#### ✅ `test_new_patient_registration`
Tests patient registration:
- Create patient with all fields
- Verify UHID generated
- Verify searchable
- Verify all fields saved

#### ✅ `test_patient_multiple_visits`
Tests patient with 6+ visits:
- Create patient
- Add 6 visits over time
- Verify timeline correct
- Verify summary includes key diagnoses

#### ✅ `test_patient_with_chronic_condition`
Tests diabetic patient care:
- Create diabetic patient
- Add multiple visits
- Add lab results (HbA1c)
- Detect care gaps (overdue HbA1c)

#### ✅ `test_patient_referral_tracking`
Tests referral source tracking:
- Create patient with referral info
- Verify referral source preserved

#### ✅ `test_patient_loyalty_points`
Tests loyalty/reputation system:
- Create patient
- Add multiple visits
- Track points/tier upgrades

### TestPatientUpdates

#### ✅ `test_update_patient_demographics`
Tests updating patient info:
- Update phone and address
- Verify changes saved

#### ✅ `test_update_preserves_history`
Tests that updates don't affect visit history:
- Add visit
- Update patient name
- Verify visit still associated

### TestPatientSearch

#### ✅ `test_search_by_name`
Tests name-based search:
- Create patients: "Rajesh Kumar", "Rajeshwari Devi"
- Search "Rajesh"
- Verify both found

#### ✅ `test_search_by_phone`
Tests phone number search

#### ✅ `test_search_by_uhid`
Tests UHID-based search

### TestPatientDeletion

#### ✅ `test_patient_deactivation`
Tests soft delete/deactivation

#### ✅ `test_patient_with_visits_cannot_be_deleted`
Tests referential integrity:
- Patient with visits can't be hard deleted
- Verify foreign key constraint

---

## 4. Communication Flow Tests (`test_communication_flow.py`)

**WhatsApp, reminders, and broadcasts**

### TestCommunicationFlow

#### ✅ `test_appointment_reminder_flow`
Tests complete reminder flow:
1. Schedule appointment reminder
2. Send via WhatsApp
3. Track delivery
4. Verify logged

#### ✅ `test_prescription_whatsapp_flow`
Tests prescription delivery:
1. Create prescription
2. Generate PDF
3. Send via WhatsApp
4. Verify delivered

#### ✅ `test_follow_up_reminder_flow`
Tests follow-up reminders:
1. Complete visit with follow-up
2. Reminder scheduled
3. Reminder sent on date
4. Verify delivered

#### ✅ `test_broadcast_to_segment`
Tests broadcast messaging:
1. Create patient segment (diabetics)
2. Send broadcast to segment
3. Verify all received

### TestReminderManagement

#### ✅ `test_multiple_reminder_types`
Tests different reminder types:
- Appointment reminders
- Medication refill reminders
- Investigation reminders

#### ✅ `test_reminder_scheduling_logic`
Tests scheduling at different intervals

### TestWhatsAppTemplates

#### ✅ `test_send_template_message`
Tests pre-approved template messages

#### ✅ `test_send_document_via_whatsapp`
Tests sending PDF documents

### TestMessageDeliveryTracking

#### ✅ `test_track_message_delivery`
Tests delivery status tracking

#### ✅ `test_failed_message_handling`
Tests handling delivery failures and retries

### TestBulkMessaging

#### ✅ `test_bulk_prescription_delivery`
Tests sending to multiple patients

#### ✅ `test_rate_limiting_bulk_messages`
Tests WhatsApp rate limits

### TestCommunicationPreferences

#### ✅ `test_opt_out_handling`
Tests respecting opt-out preferences

#### ✅ `test_language_preference`
Tests sending in patient's preferred language

---

## 5. Analytics Flow Tests (`test_analytics_flow.py`)

**Practice analytics, metrics, and reporting**

### TestAnalyticsFlow

#### ✅ `test_daily_summary_accuracy`
Tests daily summary generation:
- Create 5 consultations today
- Verify summary shows 5 consultations
- Verify metrics accurate

#### ✅ `test_revenue_calculation`
Tests revenue tracking:
- Multiple visits with amounts
- Calculate total revenue
- Calculate average per visit

#### ✅ `test_patient_acquisition_tracking`
Tests referral source tracking:
- Patients from different sources
- Calculate acquisition breakdown
- Verify percentages

#### ✅ `test_retention_metrics`
Tests patient retention:
- Track follow-up completion
- Calculate retention rate
- Identify missed follow-ups

### TestPracticeMetrics

#### ✅ `test_patient_growth_over_time`
Tests patient growth tracking

#### ✅ `test_consultation_volume_by_day`
Tests daily consultation counts

#### ✅ `test_top_diagnoses_report`
Tests most common diagnoses

### TestDoctorPerformanceMetrics

#### ✅ `test_doctor_consultation_metrics`
Tests per-doctor metrics

#### ✅ `test_average_consultation_duration`
Tests average duration calculations

### TestBusinessIntelligence

#### ✅ `test_peak_hours_analysis`
Tests identifying busy hours

#### ✅ `test_patient_lifetime_value`
Tests calculating patient LTV

---

## 6. Audit Compliance Tests (`test_audit_compliance.py`)

**Audit logging, chain integrity, consent management**

### TestAuditCompliance

#### ✅ `test_all_actions_logged`
Tests comprehensive audit logging:
- Start consultation → logged
- Generate prescription → logged
- Complete consultation → logged
- All events have required fields

#### ✅ `test_chain_integrity_maintained`
Tests blockchain-style hash chain:
- Multiple events
- Each references previous hash
- Verify chain intact
- Detect tampering

#### ✅ `test_consent_workflow`
Tests consent management:
1. Request consent
2. Patient signs
3. Verify active
4. Withdraw consent

#### ✅ `test_legal_export_format`
Tests legal compliance export:
- Generate export
- Verify format correct
- Includes all required data

### TestDataAccessControl

#### ✅ `test_patient_access_logging`
Tests access logging for patient records

#### ✅ `test_prescription_access_logging`
Tests prescription view/export logging

#### ✅ `test_unauthorized_access_prevention`
Tests blocking unauthorized access

### TestDataRetention

#### ✅ `test_archive_old_records`
Tests archival of old records

### TestComplianceReporting

#### ✅ `test_hipaa_compliance_report`
Tests HIPAA audit report generation

#### ✅ `test_data_breach_notification`
Tests breach detection and notification

### TestConsentManagement

#### ✅ `test_consent_expiration`
Tests expired consent handling

#### ✅ `test_granular_consent`
Tests different consent types

---

## 7. Error Scenarios Tests (`test_error_scenarios.py`)

**Error handling, recovery, and resilience**

### TestErrorScenarios

#### ✅ `test_database_connection_lost`
Tests DB disconnect recovery:
- Close connection
- Verify reconnection works
- Verify graceful error handling

#### ✅ `test_database_locked_error`
Tests handling locked database

#### ✅ `test_llm_service_unavailable`
Tests LLM service failure:
- LLM down
- Verify fallback behavior
- System continues working

#### ✅ `test_whatsapp_delivery_failure`
Tests WhatsApp failure:
- Delivery fails
- Verify retry queued
- Track failure

#### ✅ `test_concurrent_patient_edit`
Tests concurrent updates:
- Two users edit same patient
- Verify conflict handling

### TestDataValidationErrors

#### ✅ `test_invalid_patient_data`
Tests validation of invalid data

#### ✅ `test_missing_required_fields`
Tests required field validation

#### ✅ `test_invalid_prescription_format`
Tests malformed JSON handling

### TestNetworkErrors

#### ✅ `test_timeout_handling`
Tests network timeout handling

#### ✅ `test_connection_error_handling`
Tests connection refused handling

### TestResourceExhaustion

#### ✅ `test_memory_limit_handling`
Tests large result sets

#### ✅ `test_disk_space_error`
Tests disk full handling

### TestTransactionRollback

#### ✅ `test_rollback_on_error`
Tests transaction rollback:
- Start transaction
- Error occurs
- Verify rollback
- No partial data saved

### TestServiceDependencyFailure

#### ✅ `test_multiple_service_failures`
Tests multiple services failing:
- WhatsApp + Analytics fail
- Core functionality still works

#### ✅ `test_partial_failure_recovery`
Tests partial failures:
- One service fails
- Others continue

### TestDataCorruption

#### ✅ `test_corrupted_json_handling`
Tests handling corrupted data

#### ✅ `test_invalid_foreign_key`
Tests referential integrity

---

## Running the Tests

### Run All Integration Tests
```bash
pytest tests/integration/ -v
```

### Run Specific Module
```bash
pytest tests/integration/test_consultation_flow.py -v
```

### Run Specific Test Class
```bash
pytest tests/integration/test_consultation_flow.py::TestFullConsultationFlow -v
```

### Run Specific Test
```bash
pytest tests/integration/test_consultation_flow.py::TestFullConsultationFlow::test_complete_consultation_happy_path -v
```

### Run with Coverage
```bash
pytest tests/integration/ --cov=src --cov-report=html
```

### Run in Parallel (faster)
```bash
pytest tests/integration/ -n auto
```

---

## Test Coverage Summary

| Category | Tests | Coverage |
|----------|-------|----------|
| Consultation Flow | 8 | Complete consultation lifecycle |
| Voice Processing | 11 | Hindi, English, Hinglish, error handling |
| Patient Lifecycle | 12 | Registration, visits, chronic care, search |
| Communication | 13 | WhatsApp, reminders, broadcasts |
| Analytics | 8 | Revenue, acquisition, retention, metrics |
| Audit & Compliance | 12 | Logging, chain integrity, consent |
| Error Handling | 15 | DB errors, service failures, network errors |
| **TOTAL** | **79** | **Comprehensive E2E coverage** |

---

## Key Features Tested

✅ **Complete Workflows**
- Patient registration → multiple visits → chronic care management
- Voice input → transcription → SOAP → prescription → WhatsApp delivery
- Consultation start → voice processing → red flags → prescription → analytics

✅ **Service Integration**
- All services wired through ServiceRegistry
- Real database operations
- Mock external services (LLM, WhatsApp, Voice)
- Event bus for inter-service communication

✅ **Data Integrity**
- Database state verified after each operation
- Audit trail completeness
- Hash chain integrity
- Referential integrity (foreign keys)

✅ **Error Handling**
- Service failures don't crash system
- Graceful degradation
- Transaction rollback on errors
- Retry mechanisms

✅ **Compliance**
- All actions logged
- Consent management
- Legal export format
- HIPAA compliance

---

## Writing New Integration Tests

### Template
```python
@pytest.mark.asyncio
async def test_my_workflow(
    clinical_flow,
    sample_patient,
    full_service_registry,
    assert_audit_logged
):
    """Test description."""
    # 1. Setup
    context = await clinical_flow.start_consultation(
        patient_id=sample_patient.id,
        doctor_id="DR001"
    )

    # 2. Execute workflow
    result = await clinical_flow.some_action()

    # 3. Verify results
    assert result is not None
    assert_audit_logged("action_name", sample_patient.id)

    # 4. Verify database state
    db = full_service_registry.get("database")
    saved = db.get_something()
    assert saved.field == expected_value
```

### Best Practices

1. **Use realistic data** - Create data that represents actual usage
2. **Verify end-to-end** - Check database state, audit logs, external services
3. **Test the happy path first** - Then add error scenarios
4. **Use helper assertions** - `assert_audit_logged`, `assert_whatsapp_sent`
5. **Clean up** - Fixtures handle cleanup automatically
6. **Name tests clearly** - Test name should describe what's being tested

---

## Dependencies

Required for integration tests:
- pytest
- pytest-asyncio
- sqlite3 (built-in)
- All DocAssist services

All mocked (no actual external calls):
- Ollama LLM
- WhatsApp API
- Voice recognition
- ChromaDB (for RAG tests)

---

## Continuous Integration

These tests should run:
- ✅ Before every commit (pre-commit hook)
- ✅ On every pull request
- ✅ Before deployment to production
- ✅ Nightly for regression testing

Expected runtime: ~2-5 minutes for all 79 tests

---

## Maintenance

When adding new features:
1. Add integration test to appropriate module
2. Update this README with test description
3. Ensure fixtures support the new feature
4. Run all integration tests to ensure no regression

---

## Contact

For questions about integration tests, contact the development team or refer to the DocAssist EMR documentation.
