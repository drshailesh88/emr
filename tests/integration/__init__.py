"""Integration tests for complete workflows.

This package contains end-to-end integration tests that verify the complete
DocAssist EMR system works correctly when all services are wired together.

Test Modules:
-------------
- conftest.py: Integration test fixtures (real DB, mock services, full registry)
- test_consultation_flow.py: Complete consultation workflows
- test_voice_to_prescription.py: Voice processing pipeline
- test_patient_lifecycle.py: Patient journey and data management
- test_communication_flow.py: WhatsApp, reminders, and broadcasts
- test_analytics_flow.py: Analytics, metrics, and reporting
- test_audit_compliance.py: Audit logging and compliance
- test_error_scenarios.py: Error handling and recovery
- test_workflows.py: Legacy workflow tests

Running Integration Tests:
--------------------------
# Run all integration tests
pytest tests/integration/

# Run specific test module
pytest tests/integration/test_consultation_flow.py

# Run specific test class
pytest tests/integration/test_consultation_flow.py::TestFullConsultationFlow

# Run specific test
pytest tests/integration/test_consultation_flow.py::TestFullConsultationFlow::test_complete_consultation_happy_path

# Run with verbose output
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=src

Test Strategy:
--------------
1. Use real SQLite databases (temporary files) for realistic testing
2. Mock external services (Ollama LLM, WhatsApp, Voice) with realistic responses
3. Wire all services through ServiceRegistry for true integration
4. Verify end-to-end workflows from user action to database/external service
5. Test error handling and recovery scenarios
6. Validate audit trails and compliance requirements
"""
